import io
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airtortilla.nucleo import (
    EJEMPLO,
    codigo_iata,
    detectar_delimitador,
    leer_reservas,
    nombre_fichero,
    parsear_fecha,
    procesar,
    resolver_localizadores,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CABECERA = "fecha_reserva;origen;destino;nombre_pasajero;localizador\n"


class PruebaLecturaCsv(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="airtortilla_")

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def escribir(self, nombre, texto, codificacion):
        ruta = os.path.join(self.carpeta, nombre)
        with open(ruta, "w", encoding=codificacion, newline="") as manejador:
            manejador.write(texto)
        return ruta

    def test_lee_utf8_con_bom(self):
        ruta = self.escribir("a.csv", CABECERA + "2026-10-02;ESPANA;FRANCIA;Jos\u00e9 Nu\u00f1ez;\n", "utf-8-sig")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0]["nombre"], "Jos\u00e9 Nu\u00f1ez")

    def test_lee_cp1252(self):
        ruta = self.escribir("b.csv", CABECERA + "2026-10-02;ESPA\u00d1A;FRANCIA;Jos\u00e9 Nu\u00f1ez;\n", "cp1252")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertTrue(reservas[0]["errores"] == [])
        self.assertEqual(reservas[0]["iata"], "FR")

    def test_lee_latin1(self):
        ruta = self.escribir("c.csv", CABECERA + "2026-10-02;ESPANA;FRANCIA;Jos\u00e9 Nu\u00f1ez;\n", "latin-1")
        self.assertEqual(leer_reservas(ruta)[0]["nombre"], "Jos\u00e9 Nu\u00f1ez")

    def test_lee_texto_pegado(self):
        reservas = leer_reservas(CABECERA + "2026-10-02;ESPANA;FRANCIA;ANA SOLO;\n", es_texto=True)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0]["fila"], 2)

    def test_fichero_vacio(self):
        ruta = self.escribir("vacio.csv", "", "utf-8")
        self.assertEqual(leer_reservas(ruta), [])

    def test_delimitadores(self):
        self.assertEqual(detectar_delimitador("a;b;c\n1;2;3"), ";")
        self.assertEqual(detectar_delimitador("a,b,c\n1,2,3"), ",")
        self.assertEqual(detectar_delimitador("a\tb\tc\n1\t2\t3"), "\t")

    def test_csv_separado_por_comas(self):
        texto = "fecha_reserva,origen,destino,nombre_pasajero\n2026-10-02,ESPANA,FRANCIA,LUCIA MORENO\n"
        ruta = self.escribir("comas.csv", texto, "utf-8")
        self.assertEqual(leer_reservas(ruta)[0]["destino"], "FRANCIA")

    def test_cabeceras_con_tildes_y_mayusculas(self):
        texto = "FECHA;Pa\u00eds Origen;Pa\u00eds Destino;Nombre del Pasajero\n2026-10-02;Espa\u00f1a;Francia;Ana Solo\n"
        ruta = self.escribir("cab.csv", texto, "utf-8")
        reserva = leer_reservas(ruta)[0]
        self.assertEqual(reserva["destino"], "Francia")
        self.assertEqual(reserva["iata"], "FR")

    def test_fechas(self):
        self.assertEqual(str(parsear_fecha("2026-10-02")), "2026-10-02")
        self.assertEqual(str(parsear_fecha("02/10/2026")), "2026-10-02")
        self.assertIsNone(parsear_fecha("no es fecha"))


class PruebaCatalogo(unittest.TestCase):
    def test_codigo_directo(self):
        self.assertEqual(codigo_iata("FR"), "FR")

    def test_sinonimos(self):
        self.assertEqual(codigo_iata("EEUU"), "US")
        self.assertEqual(codigo_iata("HOLANDA"), "NL")

    def test_sin_tildes(self):
        self.assertEqual(codigo_iata("Espa\u00f1a"), "ES")
        self.assertEqual(codigo_iata("japon"), "JP")

    def test_pais_desconocido(self):
        self.assertIsNone(codigo_iata("NARNIA"))

    def test_catalogo_igual_al_de_index_html(self):
        html = io.open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
        catalogo = re.search(r'var CATALOGO = "([^"]+)"', html).group(1)
        web = {}
        for trozo in catalogo.split("|"):
            nombre, codigo = trozo.rsplit(" ", 1)
            web[nombre] = codigo
        from airtortilla.nucleo import PAISES

        self.assertEqual(PAISES, web)

    def test_destinos_del_ejemplo_catalogados(self):
        for reserva in leer_reservas(EJEMPLO, es_texto=True):
            if reserva["destino"] != "NARNIA":
                self.assertIsNotNone(reserva["iata"], reserva["destino"])


class PruebaAgrupacion(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="airtortilla_")
        self.salida = os.path.join(self.carpeta, "salida")
        self.entrada = self.escribir(
            "e.csv",
            CABECERA
            + "2026-10-02;ESPANA;FRANCIA;ANA SOLO;\n"
            + "2026-10-02;ITALIA;FRANCIA;LUCA BIANCHI;\n"
            + "2026-10-02;ESPANA;JAPON;KENJI SATO;\n"
            + "2026-10-05;ESPANA;FRANCIA;ANA SOLO;\n",
        )

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def escribir(self, nombre, texto):
        ruta = os.path.join(self.carpeta, nombre)
        with open(ruta, "w", encoding="utf-8", newline="") as manejador:
            manejador.write(texto)
        return ruta

    def test_un_fichero_por_pais_y_fecha(self):
        resultado = procesar(self.entrada, self.salida)
        nombres = sorted(f["nombre"] for f in resultado["ficheros"])
        self.assertEqual(
            nombres,
            ["AirTortilla_FR_2026_10_02.csv", "AirTortilla_FR_2026_10_05.csv", "AirTortilla_JP_2026_10_02.csv"],
        )

    def test_formato_del_nombre(self):
        resultado = procesar(self.entrada, self.salida)
        for fichero in resultado["ficheros"]:
            partes = fichero["nombre"][:-4].split("_")
            self.assertEqual(partes[0], "AirTortilla")
            self.assertEqual([len(partes[1]), len(partes[2]), len(partes[3]), len(partes[4])], [2, 4, 2, 2])

    def test_reservas_del_mismo_grupo_en_un_fichero(self):
        procesar(self.entrada, self.salida)
        ruta = os.path.join(self.salida, "AirTortilla_FR_2026_10_02.csv")
        lineas = [l for l in io.open(ruta, encoding="utf-8").read().splitlines() if l.strip()]
        self.assertEqual(len(lineas), 3)

    def test_linea_invalida_no_genera_fichero(self):
        entrada = self.escribir("i.csv", CABECERA + "2026-10-02;ESPANA;NARNIA;PABLO GARRIDO;\n")
        resultado = procesar(entrada, self.salida)
        self.assertEqual([f["nombre"] for f in resultado["ficheros"]], [])
        self.assertEqual(len(resultado["descartadas"]), 1)

    def test_modalidad_linea_a_linea(self):
        resultado = procesar(self.entrada, self.salida, linea=4)
        self.assertEqual(len(resultado["ficheros"]), 1)
        ruta = os.path.join(self.salida, "AirTortilla_JP_2026_10_02.csv")
        lineas = [l for l in io.open(ruta, encoding="utf-8").read().splitlines() if l.strip()]
        self.assertEqual(len(lineas), 2)

    def test_nombre_fichero(self):
        self.assertEqual(nombre_fichero("ES", parsear_fecha("2026-03-07")), "AirTortilla_ES_2026_03_07")


class PruebaCsvEjemplo(unittest.TestCase):
    def test_tiene_reservas(self):
        self.assertGreater(len(leer_reservas(EJEMPLO, es_texto=True)), 50)

    def test_tres_casos_de_coincidencia(self):
        reservas = leer_reservas(EJEMPLO, es_texto=True)
        resolver_localizadores(reservas)
        localizadores = {r["localizador"] for r in reservas if r["coincidencia"]}
        self.assertGreaterEqual(len(localizadores), 3)

    def test_un_grupo_de_cinco(self):
        reservas = leer_reservas(EJEMPLO, es_texto=True)
        resolver_localizadores(reservas)
        self.assertEqual(max(r["viajeros"] for r in reservas), 5)

    def test_dos_lineas_invalidas(self):
        reservas = leer_reservas(EJEMPLO, es_texto=True)
        self.assertEqual(len([r for r in reservas if r["errores"]]), 2)

    def test_ids_unicos(self):
        reservas = leer_reservas(EJEMPLO, es_texto=True)
        ids = [r["id_reserva"] for r in reservas]
        self.assertEqual(len(ids), len(set(ids)))

    def test_genera_28_ficheros(self):
        carpeta = tempfile.mkdtemp(prefix="airtortilla_")
        try:
            resultado = procesar(EJEMPLO, os.path.join(carpeta, "salida"), es_texto=True)
            self.assertEqual(len(resultado["ficheros"]), 28)
            self.assertEqual(resultado["informe"], {"leidas": 52, "validas": 50, "con_localizador": 17, "descartadas": 2})
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
