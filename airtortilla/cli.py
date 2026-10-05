import argparse
import os
import sys

from .lector_csv import leer_reservas
from .procesador import procesar_fichero, reiniciar_directorio

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ENTRADA = os.path.join(RAIZ, "data")
DIR_SALIDA = os.path.join(RAIZ, "data", "salida")
CSV_POR_DEFECTO = os.path.join(DIR_ENTRADA, "reservas_entrada.csv")


def _crear_csv_ejemplo(ruta):
    from .datos_ejemplo import obtener_lineas_csv

    directorio = os.path.dirname(os.path.abspath(ruta))
    if directorio and not os.path.isdir(directorio):
        os.makedirs(directorio)
    with open(ruta, "w", encoding="utf-8", newline="") as manejador:
        manejador.write(obtener_lineas_csv())
    return ruta


def comando_generar(args):
    origen = args.fichero or CSV_POR_DEFECTO
    if not os.path.isfile(origen):
        _crear_csv_ejemplo(origen)
        print("CSV de ejemplo creado en " + origen)
    destino = args.salida or DIR_SALIDA
    reiniciar_directorio(destino)
    resultado = procesar_fichero(
        origen, destino, solo_linea=args.linea if args.linea else None
    )
    print("Modo: {0}".format(resultado["modo"]))
    print("Fichero de entrada: {0}".format(resultado["origen"]))
    print("Directorio de salida: {0}".format(resultado["directorio_salida"]))
    print("")
    for entrada in resultado["detalle"]:
        print("[{0}] {1}".format(entrada["tipo"], entrada["texto"]))
    print("")
    for pais in resultado["resumen_paises"]:
        print("Pais {0} ({1}): {2} reserva(s)".format(pais["pais"], pais["iata"], pais["reservas"]))
        for ruta in pais["ficheros"]:
            print("   " + ruta)
    informe = resultado["informe"]
    print("")
    print("Leidas {0} | Validas {1} | Con localizador {2} | Descartadas {3}".format(
        informe["total_leidas"],
        informe["total_validas"],
        informe["total_con_localizador"],
        informe["total_invalidas"],
    ))
    return 0


def comando_web(args):
    from .servidor import lanzar

    lanzar(args.puerto, args.host)
    return 0


def construir_parser():
    parser = argparse.ArgumentParser(
        prog="airtortilla", description="AirTortilla - reservas por pais de destino"
    )
    sub = parser.add_subparsers(dest="comando")
    generar = sub.add_parser("generar", help="Genera los ficheros CSV desde la terminal")
    generar.add_argument("-f", "--fichero", default="", help="CSV de entrada")
    generar.add_argument("-s", "--salida", default="", help="Directorio de salida")
    generar.add_argument("-l", "--linea", type=int, default=0, help="Procesa solo esa linea")
    generar.set_defaults(func=comando_generar)
    web = sub.add_parser("web", help="Abre la interfaz web")
    web.add_argument("-p", "--puerto", type=int, default=8000)
    web.add_argument("--host", default="127.0.0.1")
    web.set_defaults(func=comando_web)
    return parser


def main(argumentos=None):
    parser = construir_parser()
    opciones = parser.parse_args(argumentos if argumentos is not None else sys.argv[1:])
    if not opciones.comando:
        opciones.comando = "generar"
        opciones.fichero = ""
        opciones.salida = ""
        opciones.linea = 0
        opciones.func = comando_generar
    return opciones.func(opciones)


if __name__ == "__main__":
    sys.exit(main())
