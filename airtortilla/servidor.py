import html
import io
import os
import posixpath
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .lector_csv import escribir_csv
from .modelos import CAMPOS_SALIDA
from .procesador import procesar_fichero, reiniciar_directorio
from .vistas import vista_error, vista_fichero, vista_indice

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ENTRADA = os.path.join(RAIZ, "data")
DIR_SALIDA = os.path.join(RAIZ, "data", "salida")
CAMPOS_CSV = ["id_reserva", "fecha_reserva", "origen", "destino", "nombre_pasajero"]

ESTADO = {"ultima_ejecucion": None, "mensaje": ""}


def asegurar_directorios():
    for carpeta in (DIR_ENTRADA, DIR_SALIDA):
        if not os.path.isdir(carpeta):
            os.makedirs(carpeta)


def listar_entradas():
    asegurar_directorios()
    nombres = [n for n in sorted(os.listdir(DIR_ENTRADA)) if n.lower().endswith(".csv")]
    return nombres


def _leer_datos_multipart(cuerpo, limite):
    partes = {}
    nombres = {}
    limite_bytes = limite.encode("latin-1", "ignore") if limite else None
    if limite_bytes and limite_bytes in cuerpo:
        segmentos = cuerpo.split(b"--" + limite_bytes)
        for segmento in segmentos[1:]:
            if segmento[:2] == b"--":
                break
            if b"\r\n\r\n" in segmento:
                cabecera, _, datos = segmento.partition(b"\r\n\r\n")
            elif b"\n\n" in segmento:
                cabecera, _, datos = segmento.partition(b"\n\n")
            else:
                continue
            texto_cabecera = cabecera.decode("utf-8", "replace")
            nombre = re.search(r'name="([^"]+)"', texto_cabecera)
            if not nombre:
                continue
            clave = nombre.group(1)
            archivo = re.search(r'filename="([^"]*)"', texto_cabecera)
            if archivo:
                nombres[clave] = archivo.group(1)
            if datos.endswith(b"\r\n"):
                datos = datos[:-2]
            elif datos.endswith(b"\n"):
                datos = datos[:-1]
            partes[clave] = datos
    return partes, nombres


def _guardar_subida(contenido, nombre_original):
    asegurar_directorios()
    destino = nombre_original
    destino = posixpath.basename(destino.replace("\\", "/"))
    if not destino.lower().endswith(".csv"):
        destino = (destino or "reservas.csv").rsplit(".", 1)[0] + ".csv"
    ruta = os.path.join(DIR_ENTRADA, destino)
    with io.open(ruta, "wb") as manejador:
        manejador.write(contenido)
    return ruta


class Manejador(BaseHTTPRequestHandler):
    server_version = "AirTortilla/1.0"

    def log_message(self, formato, *argumentos):
        pass

    def _enviar(self, cuerpo_html, codigo=200, tipo="text/html; charset=utf-8"):
        datos = cuerpo_html.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        partes = urlparse(self.path)
        ruta = partes.path
        consulta = parse_qs(partes.query)
        if ruta == "/":
            mensaje = ESTADO["mensaje"]
            ESTADO["mensaje"] = ""
            cuerpo = vista_indice(
                listar_entradas(), DIR_SALIDA, ESTADO["ultima_ejecucion"], mensaje
            )
            self._enviar(cuerpo)
        elif ruta.startswith("/fichero/"):
            nombre = posixpath.basename(ruta[len("/fichero/") :])
            self._enviar(self._leer_fichero_salida(nombre, como_html=True))
        elif ruta.startswith("/descargar/"):
            nombre = posixpath.basename(ruta[len("/descargar/") :])
            ruta_fichero = os.path.join(DIR_SALIDA, nombre)
            if not os.path.isfile(ruta_fichero):
                self._enviar(vista_error("El fichero no existe todavia."), 404)
                return
            with open(ruta_fichero, "rb") as manejador:
                datos = manejador.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="{0}"'.format(nombre))
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)
        elif ruta == "/salida":
            self._enviar(self._listado_salida())
        else:
            self._enviar(vista_error("Ruta no encontrada: " + ruta), 404)

    def do_POST(self):
        partes = urlparse(self.path)
        ruta = partes.path
        longitud = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(longitud) if longitud else b""
        tipo = self.headers.get("Content-Type") or ""
        limite = ""
        if "boundary=" in tipo:
            limite = tipo.split("boundary=")[1].strip().strip('"')
        if ruta == "/procesar":
            self._procesar(cuerpo, limite)
        elif ruta == "/limpiar":
            borrados = reiniciar_directorio(DIR_SALIDA)
            ESTADO["ultima_ejecucion"] = None
            ESTADO["mensaje"] = "OK Se han borrado {0} fichero(s) generado(s)".format(borrados)
            self._redirigir("/")
        else:
            self._enviar(vista_error("Ruta no encontrada: " + ruta), 404)

    def _procesar(self, cuerpo, limite):
        partes, nombres = _leer_datos_multipart(cuerpo, limite)
        if not partes:
            self._enviar(vista_error("No se han recibido datos del formulario"), 400)
            return
        modalidad = (partes.get("modalidad", b"TOTAL").decode("utf-8", "replace") or "TOTAL").upper()
        linea_texto = partes.get("linea", b"1").decode("utf-8", "replace").strip() or "1"
        subida = partes.get("fichero_subido", b"")
        nombre_servidor = partes.get("fichero_servidor", b"").decode("utf-8", "replace").strip()
        try:
            linea = int(linea_texto)
        except ValueError:
            self._enviar(vista_error("El numero de linea no es valido"), 400)
            return
        if subida:
            nombre_original = nombres.get("fichero_subido", "").strip()
            if not nombre_original:
                nombre_original = "reservas_subidas.csv"
            try:
                ruta = _guardar_subida(subida, nombre_original)
            except OSError as error:
                self._enviar(vista_error("No se pudo guardar el fichero subido: " + str(error)), 400)
                return
        else:
            if not nombre_servidor:
                self._enviar(vista_error("Selecciona un fichero de entrada"), 400)
                return
            ruta = os.path.join(DIR_ENTRADA, posixpath.basename(nombre_servidor))
        if not os.path.isfile(ruta):
            self._enviar(vista_error("El fichero de entrada no existe: " + ruta), 400)
            return
        reiniciar_directorio(DIR_SALIDA)
        try:
            if modalidad == "LINEA":
                resultado = procesar_fichero(ruta, DIR_SALIDA, solo_linea=linea)
            else:
                resultado = procesar_fichero(ruta, DIR_SALIDA)
        except Exception as error:
            self._enviar(vista_error("Error durante el proceso: " + str(error)), 500)
            return
        ESTADO["ultima_ejecucion"] = resultado
        ESTADO["mensaje"] = "OK Proceso finalizado en modalidad {0}".format(resultado["modo"])
        self._redirigir("/")

    def _listado_salida(self):
        asegurar_directorios()
        filas = []
        for nombre in sorted(os.listdir(DIR_SALIDA)):
            if not nombre.lower().endswith(".csv"):
                continue
            completa = os.path.join(DIR_SALIDA, nombre)
            filas.append(
                "<tr><td><code>{0}</code></td><td>{1} bytes</td>"
                "<td><a class='boton-enlace' href='/fichero/{0}'>Ver</a></td></tr>".format(
                    html.escape(nombre), os.path.getsize(completa)
                )
            )
        cuerpo = (
            "<div class='panel'><h2>Ficheros en {0}</h2><table><tr><th>Fichero</th>"
            "<th>Tamano</th><th></th></tr>{1}</table></div>"
        ).format(html.escape(DIR_SALIDA), "".join(filas))
        return "<html><head><meta charset='utf-8'><title>Ficheros</title></head>"
        "<body style='font-family:Segoe UI;background:#0f172a;color:#e2e8f0;padding:24px'>"
        "<a href='/' style='color:#38bdf8'>Volver</a>" + cuerpo + "</body></html>"

    def _leer_fichero_salida(self, nombre, como_html=False):
        ruta = os.path.join(DIR_SALIDA, posixpath.basename(nombre))
        if not os.path.isfile(ruta):
            return vista_error("El fichero " + nombre + " no existe todavia.")
        with io.open(ruta, "r", encoding="utf-8") as manejador:
            contenido = manejador.read()
        if como_html:
            return vista_fichero(nombre, contenido)
        return contenido

    def _redirigir(self, destino):
        self.send_response(303)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()


def crear_servidor(puerto=8000, host="127.0.0.1"):
    asegurar_directorios()
    if not os.path.isdir(DIR_ENTRADA):
        os.makedirs(DIR_ENTRADA)
    return ThreadingHTTPServer((host, puerto), Manejador)


def lanzar(puerto=8000, host="127.0.0.1"):
    servidor = crear_servidor(puerto, host)
    print("AirTortilla escuchando en http://{0}:{1}".format(host, puerto))
    print("Entradas en: " + DIR_ENTRADA)
    print("Salidas  en: " + DIR_SALIDA)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
    finally:
        servidor.server_close()


__all__ = [
    "crear_servidor",
    "lanzar",
    "escribir_csv",
    "CAMPOS_CSV",
    "CAMPOS_SALIDA",
]
