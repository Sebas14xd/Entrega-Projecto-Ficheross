import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airtortilla.datos_ejemplo import obtener_lineas_csv
from airtortilla.lector_csv import leer_reservas
from airtortilla.modelos import parsear_fecha, resolver_localizadores
from airtortilla.paises import codigo_iata
from airtortilla.procesador import nombre_fichero, procesar_fichero


class PruebaPaises(unittest.TestCase):
    def test_codigo_de_pais_con_tildes(self):
        espana = "Espa" + chr(241) + "a"
        self.assertEqual(codigo_iata(espana), "ES")
        self.assertEqual(codigo_iata(espana.lower()), "ES")
        self.assertEqual(codigo_iata("ESTADOS UNIDOS"), "US")
        self.assertEqual(codigo_iata("Japon"), "JP")

    def test_codigo_directo(self):
        self.assertEqual(codigo_iata("FR"), "FR")

    def test_pais_desconocido(self):
        self.assertIsNone(codigo_iata("NARNIA"))


class PruebaFechas(unittest.TestCase):
    def test_formatos_aceptados(self):
        esperado = parsear_fecha("2026-10-02")
        self.assertEqual(str(esperado), "2026-10-02")
        self.assertEqual(str(parsear_fecha("02/10/2026")), "2026-10-02")
        self.assertEqual(str(parsear_fecha("02-10-2026")), "2026-10-02")
        self.assertEqual(str(parsear_fecha("2026/10/02")), "2026-10-02")

    def test_fecha_invalida(self):
        self.assertIsNone(parsear_fecha("no es una fecha"))


class PruebaNombreFichero(unittest.TestCase):
    def test_formato_requerido(self):
        fecha = parsear_fecha("2026-03-07")
        self.assertEqual(nombre_fichero("ES", fecha), "AirTortilla_ES_2026_03_07")


class PruebaProcesoTotal(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="airtortilla_pruebas_")
        self.entrada = os.path.join(self.carpeta, "reservas.csv")
        self.salida = os.path.join(self.carpeta, "salida")
        with open(self.entrada, "w", encoding="utf-8", newline="") as manejador:
            manejador.write(obtener_lineas_csv())

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def test_se_genera_un_fichero_por_pais_destino(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        nombres = {item["nombre"] for item in resultado["ficheros"]}
        self.assertIn("AirTortilla_FR_2026_10_02.csv", nombres)
        self.assertIn("AirTortilla_JP_2026_10_02.csv", nombres)
        self.assertIn("AirTortilla_ES_2026_10_04.csv", nombres)
        self.assertIn("AirTortilla_US_2026_10_03.csv", nombres)

    def test_todos_los_ficheros_cumplen_el_formato(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        for item in resultado["ficheros"]:
            partes = item["nombre"][:-4].split("_")
            self.assertEqual(partes[0], "AirTortilla")
            self.assertEqual(len(partes[1]), 2)
            self.assertEqual(len(partes[2]), 4)
            self.assertEqual(len(partes[3]), 2)
            self.assertEqual(len(partes[4]), 2)

    def test_ids_unicos(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        ids = [entrada["id_reserva"] for entrada in resultado["detalle"] if entrada["tipo"] != "ERROR"]
        self.assertEqual(len(ids), len(set(ids)))

    def test_grupo_de_cinco_coincidentes(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        coincidencias = [
            entrada for entrada in resultado["detalle"] if entrada["tipo"] == "COINCIDENCIA"
        ]
        grupo_cinco = [
            entrada for entrada in coincidencias if "5 viajeros" in entrada["texto"]
        ]
        self.assertEqual(len(grupo_cinco), 5)
        localizadores = {
            entrada["texto"].split("LOCALIZADOR ")[1].split(" ")[0]
            for entrada in grupo_cinco
        }
        self.assertEqual(len(localizadores), 1)

    def test_existen_tres_casos_de_coincidencia(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        reservas = leer_reservas(self.entrada)
        resolver_localizadores([r for r in reservas if r.valida])
        localizadores = {r.localizador for r in reservas if r.coincidencia}
        self.assertGreaterEqual(len(localizadores), 3)

    def test_localizador_solo_si_hay_repeticion(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        unicicas = [
            entrada for entrada in resultado["detalle"]
            if entrada["tipo"] == "OK" and "LOCALIZADOR" not in entrada["texto"]
        ]
        self.assertGreater(len(unicicas), 0)

    def test_lineas_invalidas_se_descartan(self):
        resultado = procesar_fichero(self.entrada, self.salida)
        errores = [entrada for entrada in resultado["detalle"] if entrada["tipo"] == "ERROR"]
        self.assertEqual(len(errores), 2)
        self.assertEqual(resultado["informe"]["total_invalidas"], 2)

    def test_reservas_validas_en_fichero_de_salida(self):
        procesar_fichero(self.entrada, self.salida)
        salida = os.path.join(self.salida, "AirTortilla_ES_2026_10_04.csv")
        with open(salida, "r", encoding="utf-8") as manejador:
            lineas = [linea for linea in manejador.read().splitlines() if linea.strip()]
        self.assertEqual(len(lineas), 4)


class PruebaProcesoLinea(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="airtortilla_linea_")
        self.entrada = os.path.join(self.carpeta, "reservas.csv")
        self.salida = os.path.join(self.carpeta, "salida")
        with open(self.entrada, "w", encoding="utf-8", newline="") as manejador:
            manejador.write(obtener_lineas_csv())

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def test_una_sola_linea_procesada(self):
        resultado = procesar_fichero(self.entrada, self.salida, solo_linea=3)
        self.assertEqual(resultado["modo"], "LINEA")
        self.assertEqual(len(resultado["detalle"]), 1)
        salida = os.path.join(self.salida, "AirTortilla_FR_2026_10_02.csv")
        self.assertTrue(os.path.isfile(salida))
        with open(salida, "r", encoding="utf-8") as manejador:
            lineas = [linea for linea in manejador.read().splitlines() if linea.strip()]
        self.assertEqual(len(lineas), 3)

    def test_linea_sin_precedentes(self):
        resultado = procesar_fichero(self.entrada, self.salida, solo_linea=2)
        self.assertEqual(len(resultado["detalle"]), 1)
        salida = os.path.join(self.salida, "AirTortilla_FR_2026_10_02.csv")
        self.assertTrue(os.path.isfile(salida))
        with open(salida, "r", encoding="utf-8") as manejador:
            lineas = [linea for linea in manejador.read().splitlines() if linea.strip()]
        self.assertEqual(len(lineas), 2)

    def test_linea_cabecera_no_procesa_nada(self):
        resultado = procesar_fichero(self.entrada, self.salida, solo_linea=1)
        self.assertEqual(resultado["detalle"], [])
        self.assertEqual(resultado["ficheros"], [])

    def test_linea_inexistente(self):
        resultado = procesar_fichero(self.entrada, self.salida, solo_linea=9999)
        self.assertEqual(resultado["detalle"], [])
        self.assertEqual(resultado["ficheros"], [])


class PruebaReinicio(unittest.TestCase):
    def test_reinicio_borra_solo_airtortilla(self):
        from airtortilla.procesador import reiniciar_directorio

        carpeta = tempfile.mkdtemp(prefix="airtortilla_reinicio_")
        try:
            with open(os.path.join(carpeta, "AirTortilla_ES_2026_01_01.csv"), "w") as m:
                m.write("x")
            with open(os.path.join(carpeta, "otro.csv"), "w") as m:
                m.write("x")
            borrados = reiniciar_directorio(carpeta)
            self.assertEqual(borrados, 1)
            self.assertTrue(os.path.isfile(os.path.join(carpeta, "otro.csv")))
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)


class PruebaInterfazWeb(unittest.TestCase):
    def setUp(self):
        import threading
        import time
        import urllib.request

        from airtortilla import servidor

        self.servidor = servidor.crear_servidor(0)
        self.url = "http://127.0.0.1:{0}".format(self.servidor.server_address[1])
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()
        time.sleep(0.4)
        self.urllib = urllib.request

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        from airtortilla import servidor

        sobrante = os.path.join(servidor.DIR_ENTRADA, "carga.csv")
        if os.path.isfile(sobrante):
            os.remove(sobrante)

    def _enviar(self, modalidad, linea, csv_texto=None):
        limite = "----LimiteAirTortilla"
        partes = []
        for clave, valor in (
            ("modalidad", modalidad),
            ("linea", str(linea)),
            ("fichero_servidor", "reservas_entrada.csv"),
        ):
            partes.append(
                (
                    "--{0}\r\nContent-Disposition: form-data; name=\"{1}\"\r\n\r\n{2}\r\n"
                ).format(limite, clave, valor).encode("utf-8")
            )
        partes.append(
            (
                "--{0}\r\nContent-Disposition: form-data; name=\"fichero_subido\"; "
                "filename=\"carga.csv\"\r\nContent-Type: text/csv\r\n\r\n"
            ).format(limite).encode("utf-8")
        )
        partes.append((csv_texto or "").encode("utf-8"))
        partes.append(("\r\n--{0}--\r\n").format(limite).encode("utf-8"))
        peticion = self.urllib.Request(
            self.url + "/procesar",
            data=b"".join(partes),
            headers={"Content-Type": "multipart/form-data; boundary=" + limite},
        )
        return self.urllib.urlopen(peticion).read().decode("utf-8")

    def test_inicio_devuelve_html(self):
        respuesta = self.urllib.urlopen(self.url + "/")
        cuerpo = respuesta.read().decode("utf-8")
        self.assertEqual(respuesta.status, 200)
        self.assertIn("AirTortilla", cuerpo)
        self.assertIn("Modalidad total", cuerpo)
        self.assertIn("Modalidad linea a linea", cuerpo)

    def test_proceso_total_muestra_el_proceso_completo(self):
        cuerpo = self._enviar("TOTAL", 2)
        self.assertIn("Detalle linea a linea", cuerpo)
        self.assertIn("Ficheros generados por pais de destino", cuerpo)
        self.assertIn("AirTortilla_FR_2026_10_02.csv", cuerpo)
        self.assertIn("LOCALIZADOR LOC-", cuerpo)

    def test_proceso_de_una_sola_linea(self):
        cuerpo = self._enviar("LINEA", 6)
        self.assertIn("Resumen por pais", cuerpo)
        self.assertIn("AirTortilla_JP_2026_10_02.csv", cuerpo)
        self.assertIn("LOCALIZADOR LOC-ANNASC", cuerpo)

    def test_fichero_subido_no_pisa_el_original(self):
        self._enviar(
            "TOTAL",
            2,
            "fecha_reserva;origen;destino;nombre_pasajero\n"
            "2027-01-05;ESPANA;JAPON;PERSONA UNICA\n",
        )
        entrada = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "reservas_entrada.csv",
        )
        with open(entrada, "r", encoding="utf-8") as manejador:
            lineas = manejador.read().splitlines()
        self.assertEqual(len(lineas), 53)
        self.assertTrue(lineas[0].startswith("fecha_reserva"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
