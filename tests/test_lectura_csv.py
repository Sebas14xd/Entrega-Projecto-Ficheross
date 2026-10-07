import os
import shutil
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airtortilla.lector_csv import detectar_delimitador, leer_reservas
from airtortilla.modelos import resolver_localizadores
from airtortilla.paises import codigo_iata, paises_soportados
from airtortilla.procesador import nombre_fichero, procesar_fichero

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_EJEMPLO = os.path.join(RAIZ, "data", "reservas_entrada.csv")

CABECERA = "fecha_reserva;origen;destino;nombre_pasajero;localizador\n"
LINEA = "2026-10-02;ESPANA;FRANCIA;Jos\u00e9 Nu\u00f1ez;\n"


class PruebaLecturaCsv(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="airtortilla_sebas_")

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def escribir(self, nombre, contenido, codificacion):
        ruta = os.path.join(self.carpeta, nombre)
        with open(ruta, "w", encoding=codificacion, newline="") as manejador:
            manejador.write(contenido)
        return ruta

    def test_lee_utf8_con_bom(self):
        ruta = self.escribir("bom.csv", CABECERA + LINEA, "utf-8-sig")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0].nombre_pasajero, "Jos\u00e9 Nu\u00f1ez")

    def test_lee_cp1252(self):
        ruta = self.escribir("windows.csv", CABECERA + LINEA, "cp1252")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0].destino, "FRANCIA")
        self.assertEqual(reservas[0].nombre_pasajero, "Jos\u00e9 Nu\u00f1ez")

    def test_lee_latin1(self):
        ruta = self.escribir("latin.csv", CABECERA + LINEA, "latin-1")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0].nombre_pasajero, "Jos\u00e9 Nu\u00f1ez")

    def test_lineas_con_acentos_no_se_descartan(self):
        ruta = self.escribir("acentos.csv", CABECERA + LINEA, "cp1252")
        reservas = leer_reservas(ruta)
        self.assertTrue(reservas[0].valida)

    def test_lee_texto_pegado(self):
        reservas = leer_reservas(CABECERA + LINEA, es_texto=True)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0].iata, "FR")

    def test_fichero_vacio_no_da_error(self):
        ruta = self.escribir("vacio.csv", "", "utf-8")
        self.assertEqual(leer_reservas(ruta), [])

    def test_delimitador_punto_y_coma(self):
        texto = "a;b;c\n1;2;3\n"
        self.assertEqual(detectar_delimitador(texto), ";")

    def test_delimitador_coma(self):
        texto = "a,b,c\n1,2,3\n"
        self.assertEqual(detectar_delimitador(texto), ",")

    def test_delimitador_tabulador(self):
        texto = "a\tb\tc\n1\t2\t3\n"
        self.assertEqual(detectar_delimitador(texto), "\t")

    def test_delimitador_barra_vertical(self):
        texto = "a|b|c\n1|2|3\n"
        self.assertEqual(detectar_delimitador(texto), "|")

    def test_lee_csv_separado_por_comas(self):
        contenido = "fecha_reserva,origen,destino,nombre_pasajero\n2026-10-02,ESPANA,FRANCIA,LUCIA MORENO\n"
        ruta = self.escribir("comas.csv", contenido, "utf-8")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0].destino, "FRANCIA")

    def test_encabezados_con_tildes_y_mayusculas(self):
        contenido = "FECHA;Pa\u00eds Origen;Pa\u00eds Destino;Nombre del Pasajero\n2026-10-02;Espa\u00f1a;Francia;Ana Solo\n"
        ruta = self.escribir("cabeceras.csv", contenido, "utf-8")
        reservas = leer_reservas(ruta)
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0].destino, "Francia")
        self.assertEqual(reservas[0].origen, "Espa\u00f1a")

    def test_encabezados_con_guion_bajo(self):
        contenido = "fecha_reserva;origen;destino;nombre_pasajero\n2026-10-02;ESPANA;FRANCIA;ANA SOLO\n"
        ruta = self.escribir("guion.csv", contenido, "utf-8")
        self.assertEqual(len(leer_reservas(ruta)), 1)

    def test_numeros_de_linea_empiezan_en_la_cabecera(self):
        contenido = CABECERA + LINEA + "2026-10-03;ITALIA;JAPON;KENJI SATO;\n"
        ruta = self.escribir("lineas.csv", contenido, "utf-8")
        reservas = leer_reservas(ruta)
        self.assertEqual([r.fila for r in reservas], [2, 3])


class PruebaCatalogoPaises(unittest.TestCase):
    def test_codigo_directo(self):
        self.assertEqual(codigo_iata("FR"), "FR")
        self.assertEqual(codigo_iata("es"), "ES")

    def test_codigo_sinonimo(self):
        self.assertEqual(codigo_iata("EEUU"), "US")
        self.assertEqual(codigo_iata("INGLATERRA"), "GB")
        self.assertEqual(codigo_iata("HOLANDA"), "NL")

    def test_codigo_sin_tildes(self):
        self.assertEqual(codigo_iata("Espa\u00f1a"), "ES")
        self.assertEqual(codigo_iata("PAISES BAJOS"), "NL")

    def test_pais_desconocido(self):
        self.assertIsNone(codigo_iata("NARNIA"))

    def test_catalogo_con_codigos_de_dos_letras(self):
        for pais in paises_soportados():
            self.assertEqual(len(codigo_iata(pais)), 2, pais)

    def test_destinos_del_csv_de_ejemplo_estan_catalogados(self):
        reservas = leer_reservas(RUTA_EJEMPLO)
        for reserva in reservas:
            if reserva.destino == "NARNIA":
                continue
            self.assertIsNotNone(
                codigo_iata(reserva.destino), "sin catalogo: " + reserva.destino
            )


class PruebaAgrupacionPorPais(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="airtortilla_agrupa_")
        self.entrada = os.path.join(self.carpeta, "reservas.csv")
        self.salida = os.path.join(self.carpeta, "salida")
        contenido = (
            CABECERA
            + "2026-10-02;ESPANA;FRANCIA;ANA SOLO;\n"
            + "2026-10-02;ITALIA;FRANCIA;LUCA BIANCHI;\n"
            + "2026-10-02;ESPANA;JAPON;KENJI SATO;\n"
            + "2026-10-05;ESPANA;FRANCIA;ANA SOLO;\n"
        )
        with open(self.entrada, "w", encoding="utf-8", newline="") as manejador:
            manejador.write(contenido)

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def test_un_fichero_por_pais_y_fecha(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        nombres = sorted(item["nombre"] for item in resultado["ficheros"])
        self.assertEqual(
            nombres,
            [
                "AirTortilla_FR_2026_10_02.csv",
                "AirTortilla_FR_2026_10_05.csv",
                "AirTortilla_JP_2026_10_02.csv",
            ],
        )

    def test_reservas_del_mismo_pais_y_fecha_comparten_fichero(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        grupos = {item["clave"]: item["fichero"] for item in resultado["grupos"]}
        self.assertEqual(grupos["FR|2026-10-02"], "AirTortilla_FR_2026_10_02.csv")

    def test_las_dos_reservas_de_francia_estan_en_su_fichero(self):
        procesar_fichero(self.entrada, self.salida)
        ruta = os.path.join(self.salida, "AirTortilla_FR_2026_10_02.csv")
        with open(ruta, "r", encoding="utf-8") as manejador:
            lineas = [linea for linea in manejador.read().splitlines() if linea.strip()]
        self.assertEqual(len(lineas), 3)

    def test_formato_del_nombre_del_fichero(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        for item in resultado["ficheros"]:
            partes = item["nombre"][:-4].split("_")
            self.assertEqual(partes[0], "AirTortilla")
            self.assertEqual(len(partes[1]), 2)
            self.assertEqual(len(partes[2]), 4)
            self.assertEqual(len(partes[3]), 2)
            self.assertEqual(len(partes[4]), 2)
            esperado = nombre_fichero(item["iata"], date.fromisoformat(item["fecha"]))
            self.assertEqual(item["nombre"], esperado + ".csv")

    def test_las_lineas_invalidas_no_generan_fichero(self):
        contenido = (
            CABECERA
            + "2026-10-02;ESPANA;NARNIA;PABLO GARRIDO;\n"
            + "2026-10-02;ESPANA;FRANCIA;ANA SOLO;\n"
        )
        entrada = os.path.join(self.carpeta, "invalidas.csv")
        with open(entrada, "w", encoding="utf-8", newline="") as manejador:
            manejador.write(contenido)
        resultado = procesar_fichero(entrada, self.salida)
        nombres = {item["nombre"] for item in resultado["ficheros"]}
        self.assertEqual(nombres, {"AirTortilla_FR_2026_10_02.csv"})


class PruebaCsvEjemplo(unittest.TestCase):
    def test_existe_el_fichero_de_ejemplo(self):
        self.assertTrue(os.path.isfile(RUTA_EJEMPLO))

    def test_tiene_cabecera_y_reservas(self):
        reservas = leer_reservas(RUTA_EJEMPLO)
        self.assertGreater(len(reservas), 50)

    def test_tres_casos_de_coincidencia(self):
        reservas = leer_reservas(RUTA_EJEMPLO)
        resolver_localizadores([r for r in reservas if r.valida])
        localizadores = {r.localizador for r in reservas if r.coincidencia}
        self.assertGreaterEqual(len(localizadores), 3)

    def test_un_caso_con_cinco_personas(self):
        reservas = leer_reservas(RUTA_EJEMPLO)
        resolver_localizadores([r for r in reservas if r.valida])
        grupos = [r.viajeros_en_grupo for r in reservas if r.coincidencia]
        self.assertEqual(max(grupos), 5)

    def test_solo_dos_lineas_invalidas(self):
        reservas = leer_reservas(RUTA_EJEMPLO)
        invalidas = [r for r in reservas if not r.valida]
        self.assertEqual(len(invalidas), 2)

    def test_se_generan_los_ficheros_del_ejemplo(self):
        carpeta = tempfile.mkdtemp(prefix="airtortilla_ejemplo_")
        try:
            salida = os.path.join(carpeta, "salida")
            resultado = procesar_fichero(RUTA_EJEMPLO, salida)
            nombres = {item["nombre"] for item in resultado["ficheros"]}
            self.assertIn("AirTortilla_FR_2026_10_02.csv", nombres)
            self.assertIn("AirTortilla_JP_2026_10_02.csv", nombres)
            self.assertEqual(len(nombres), 28)
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
