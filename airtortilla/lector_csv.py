import csv
import io
import os

from .modelos import Reserva, parsear_fecha
from .paises import normalizar_texto

ALIAS_CAMPOS = {
    "FECHA": "fecha_reserva",
    "FECHA RESERVA": "fecha_reserva",
    "FECHA DE LA RESERVA": "fecha_reserva",
    "FECHA RESERVACION": "fecha_reserva",
    "FECHA DE RESERVA": "fecha_reserva",
    "ORIGEN": "origen",
    "CIUDAD ORIGEN": "origen",
    "PAIS ORIGEN": "origen",
    "DESTINO": "destino",
    "CIUDAD DESTINO": "destino",
    "PAIS DESTINO": "destino",
    "NOMBRE": "nombre_pasajero",
    "NOMBRE DEL PASAJERO": "nombre_pasajero",
    "NOMBRE PASAJERO": "nombre_pasajero",
    "PASAJERO": "nombre_pasajero",
    "LOCALIZADOR": "localizador",
    "BOOKING ID": "id_reserva",
    "ID": "id_reserva",
    "ID RESERVA": "id_reserva",
    "REFERENCIA": "localizador",
}


def detectar_delimitador(texto):
    muestras = [linea for linea in texto.splitlines()[:25] if linea.strip()]
    mejor = ","
    mejor_cantidad = -1
    for candidato in (";", ",", "\t", "|"):
        cantidad = sum(linea.count(candidato) for linea in muestras)
        if cantidad > mejor_cantidad:
            mejor_cantidad = cantidad
            mejor = candidato
    return mejor


def normalizar_encabezados(encabezados):
    mapa = {}
    for indice, bruto in enumerate(encabezados):
        clave = normalizar_texto(str(bruto).replace("_", " "))
        if clave in ALIAS_CAMPOS:
            mapa[ALIAS_CAMPOS[clave]] = indice
    if "fecha_reserva" not in mapa:
        for indice, bruto in enumerate(encabezados):
            clave = normalizar_texto(str(bruto).replace("_", " "))
            if "FECHA" in clave:
                mapa["fecha_reserva"] = indice
                break
    return mapa


CODIFICACIONES = ["utf-8", "cp1252", "latin-1"]
MARCA_BOM = b"\xef\xbb\xbf"


def leer_texto(ruta):
    with open(ruta, "rb") as manejador:
        bruto = manejador.read()
    if bruto.startswith(MARCA_BOM):
        bruto = bruto[len(MARCA_BOM) :]
    for codificacion in CODIFICACIONES:
        try:
            return bruto.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return bruto.decode("latin-1", "replace")


def leer_reservas(ruta_o_texto, es_texto=False):
    if es_texto:
        contenido = ruta_o_texto
    else:
        contenido = leer_texto(ruta_o_texto)
    if not contenido.strip():
        return []
    delimitador = detectar_delimitador(contenido)
    filas = list(csv.reader(io.StringIO(contenido), delimiter=delimitador))
    filas = [fila for fila in filas if any(celda.strip() for celda in fila)]
    if not filas:
        return []
    mapa = normalizar_encabezados(filas[0])
    cuerpo = filas[1:] if mapa else filas
    reservas = []
    repeticiones = {}
    for indice, fila in enumerate(cuerpo):
        def valor(campo):
            posicion = mapa.get(campo)
            if posicion is None or posicion >= len(fila):
                return ""
            return fila[posicion]

        reserva = Reserva(
            fila=indice + (2 if mapa else 1),
            indice=indice,
            fecha=parsear_fecha(valor("fecha_reserva")),
            origen=valor("origen"),
            destino=valor("destino"),
            nombre=valor("nombre_pasajero"),
            localizador_entrada=valor("localizador"),
        )
        base = "|".join(
            [
                reserva.fecha.isoformat() if reserva.fecha else "sin-fecha",
                normalizar_texto(reserva.origen),
                normalizar_texto(reserva.destino),
                normalizar_texto(reserva.nombre_pasajero),
            ]
        )
        repeticiones[base] = repeticiones.get(base, 0)
        reserva.asignar_identificadores(repeticiones[base])
        repeticiones[base] += 1
        if reserva.localizador_entrada:
            reserva.localizador = reserva.localizador_entrada.upper()
        reserva.validar()
        reservas.append(reserva)
    return reservas


def escribir_csv(ruta, registros, campos):
    directorio = os.path.dirname(os.path.abspath(ruta))
    if directorio and not os.path.isdir(directorio):
        os.makedirs(directorio)
    with io.open(ruta, "w", encoding="utf-8", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        for registro in registros:
            fila = {campo: registro.get(campo, "") for campo in campos}
            escritor.writerow(fila)
    return ruta


def contenido_csv_texto(registros, campos):
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=campos, delimiter=";")
    escritor.writeheader()
    for registro in registros:
        escritor.writerow({campo: registro.get(campo, "") for campo in campos})
    return buffer.getvalue()
