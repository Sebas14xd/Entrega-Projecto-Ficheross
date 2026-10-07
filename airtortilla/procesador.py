import io
import os
from datetime import datetime

from .lector_csv import contenido_csv_texto, escribir_csv, leer_reservas
from .modelos import CAMPOS_SALIDA, resolver_localizadores
from .paises import nombre_pais_por_iata

PREFIJO = "AirTortilla"


def nombre_fichero(iata, fecha):
    return "{0}_{1}_{2:04d}_{3:02d}_{4:02d}".format(
        PREFIJO, iata, fecha.year, fecha.month, fecha.day
    )


def clave_agrupacion_destino(reserva):
    return "{0}|{1}".format(
        reserva.iata, reserva.fecha.isoformat() if reserva.fecha else "sin-fecha"
    )


def generar_informe(reservas):
    return {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_leidas": len(reservas),
        "total_validas": len([r for r in reservas if r.valida]),
        "total_invalidas": len([r for r in reservas if not r.valida]),
        "total_con_localizador": len([r for r in reservas if r.coincidencia]),
    }


def procesar_fichero(ruta_entrada, directorio_salida, solo_linea=None, registra_log=True):
    reservas = leer_reservas(ruta_entrada)
    return procesar_reservas(
        reservas,
        directorio_salida,
        solo_linea=solo_linea,
        origen_nombre=os.path.basename(ruta_entrada),
        registra_log=registra_log,
    )


def procesar_reservas(
    reservas,
    directorio_salida,
    solo_linea=None,
    origen_nombre="reservas.csv",
    registra_log=True,
):
    paso = "TOTAL" if solo_linea is None else "LINEA"
    acumuladas = []
    if paso == "TOTAL":
        seleccionadas = list(reservas)
    else:
        seleccionadas = [r for r in reservas if r.fila == solo_linea]
        acumuladas = [r for r in reservas if r.fila < solo_linea and r.valida]
        _recalcular_fichero_destino(acumuladas)
    resolver_localizadores(acumuladas + [r for r in seleccionadas if r.valida])

    grupos = {}
    descartadas = []
    for reserva in seleccionadas:
        if not reserva.valida:
            descartadas.append(reserva)
            continue
        grupos.setdefault(clave_agrupacion_destino(reserva), []).append(reserva)

    log = []
    ficheros = []
    resumen_paises = {}
    for clave in sorted(grupos):
        miembros = grupos[clave]
        cabecera = miembros[0]
        nombre = nombre_fichero(cabecera.iata, cabecera.fecha)
        for reserva in miembros:
            reserva.fichero_destino = nombre
        ruta = os.path.join(directorio_salida, nombre + ".csv")
        registros = [r.como_diccionario() for r in miembros]
        if paso == "LINEA":
            previos = [
                r
                for r in reservas
                if r.fila < solo_linea and r.valida and r.fichero_destino == nombre
            ]
            registros = [r.como_diccionario() for r in previos] + registros
        escribir_csv(ruta, registros, CAMPOS_SALIDA)
        pais = nombre_pais_por_iata(cabecera.iata)
        resumen_paises.setdefault(
            cabecera.iata,
            {"pais": pais, "iata": cabecera.iata, "reservas": 0, "ficheros": []},
        )
        resumen_paises[cabecera.iata]["reservas"] += len(miembros)
        resumen_paises[cabecera.iata]["ficheros"].append(ruta)
        ficheros.append(
            {
                "nombre": nombre + ".csv",
                "ruta": ruta,
                "iata": cabecera.iata,
                "pais": pais,
                "fecha": cabecera.fecha.isoformat(),
                "lineas": len(registros),
                "modo": paso,
            }
        )
        if registra_log:
            log.append(
                "Grupo {0} ({1}) -> {2} con {3} reserva(s)".format(
                    cabecera.iata, pais, nombre + ".csv", len(registros)
                )
            )

    for reserva in descartadas:
        if registra_log:
            log.append(
                "Linea {0} descartada, no genera fichero: {1}".format(
                    reserva.fila, "; ".join(reserva.errores)
                )
            )

    detalle = []
    for reserva in seleccionadas:
        if not reserva.valida:
            detalle.append(
                {
                    "tipo": "ERROR",
                    "fila": reserva.fila,
                    "id_reserva": reserva.id_reserva,
                    "texto": "Linea {0} descartada: {1}".format(
                        reserva.fila, "; ".join(reserva.errores)
                    ),
                }
            )
        else:
            texto = "Linea {0} | {1} | {2} -> {3} | destino {4} ({5}) | fichero {6}".format(
                reserva.fila,
                reserva.nombre_pasajero,
                reserva.origen,
                reserva.destino,
                reserva.iata,
                reserva.id_reserva,
                reserva.fichero_destino + ".csv",
            )
            if reserva.coincidencia:
                texto += " | LOCALIZADOR {0} ({1} viajeros)".format(
                    reserva.localizador, reserva.viajeros_en_grupo
                )
            detalle.append(
                {
                    "tipo": "COINCIDENCIA" if reserva.coincidencia else "OK",
                    "fila": reserva.fila,
                    "id_reserva": reserva.id_reserva,
                    "texto": texto,
                }
            )

    resumen_grupos = []
    for clave, miembros in grupos.items():
        cabecera = miembros[0]
        resumen_grupos.append(
            {
                "clave": clave,
                "iata": cabecera.iata,
                "pais": nombre_pais_por_iata(cabecera.iata),
                "fecha": cabecera.fecha.isoformat(),
                "reservas": len(miembros),
                "fichero": miembros[0].fichero_destino + ".csv",
            }
        )
    resumen_grupos.sort(key=lambda item: (item["iata"], item["fecha"]))

    return {
        "modo": paso,
        "linea_solicitada": solo_linea,
        "origen": origen_nombre,
        "directorio_salida": os.path.abspath(directorio_salida),
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "log": log,
        "detalle": detalle,
        "ficheros": ficheros,
        "resumen_paises": sorted(
            resumen_paises.values(), key=lambda item: item["iata"]
        ),
        "grupos": resumen_grupos,
        "informe": generar_informe(seleccionadas),
        "contenido": {
            item["nombre"]: contenido_csv_texto(
                _leer_registros(item["ruta"]), CAMPOS_SALIDA
            )
            for item in ficheros
        },
    }


def _recalcular_fichero_destino(reservas):
    for reserva in reservas:
        if reserva.iata and reserva.fecha:
            reserva.fichero_destino = nombre_fichero(reserva.iata, reserva.fecha)
        else:
            reserva.fichero_destino = PREFIJO + "_ERROR"


def _leer_registros(ruta):
    import csv

    registros = []
    with io.open(ruta, "r", encoding="utf-8-sig", newline="") as manejador:
        for fila in csv.DictReader(manejador, delimiter=";"):
            registros.append(fila)
    return registros


def reiniciar_directorio(directorio):
    if not os.path.isdir(directorio):
        os.makedirs(directorio)
        return 0
    borrados = 0
    for nombre in os.listdir(directorio):
        if nombre.startswith(PREFIJO) and nombre.lower().endswith(".csv"):
            os.remove(os.path.join(directorio, nombre))
            borrados += 1
    return borrados
