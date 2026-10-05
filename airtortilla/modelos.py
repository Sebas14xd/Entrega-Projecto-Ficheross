import hashlib
import re

from .paises import codigo_iata, normalizar_texto

CAMPOS_ENTRADA = [
    "fecha_reserva",
    "origen",
    "destino",
    "nombre_pasajero",
    "localizador",
]

CAMPOS_SALIDA = [
    "id_reserva",
    "fecha_reserva",
    "destino",
    "destino_iata",
    "origen",
    "nombre_pasajero",
    "localizador",
    "coincidencia",
    "viajero_en_grupo",
]

ALFABETO = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

FORMATOS_FECHA = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
]


def _hash_corto(texto, longitud=8):
    digest = hashlib.sha1(texto.encode("utf-8")).digest()
    numero = int.from_bytes(digest[:12], "big")
    salida = []
    for _ in range(longitud):
        numero, resto = divmod(numero, len(ALFABETO))
        salida.append(ALFABETO[resto])
    return "".join(salida)


def _slug(texto, maximo=28):
    limpio = re.sub(r"[^A-Z0-9]+", "", normalizar_texto(texto))
    return limpio[:maximo] if limpio else "X"


def parsear_fecha(valor):
    texto = str(valor or "").strip()
    if not texto:
        return None
    for formato in FORMATOS_FECHA:
        try:
            from datetime import datetime

            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    partes = re.split(r"[-/.\s]", texto)
    if len(partes) == 3:
        try:
            from datetime import date

            if len(partes[0]) == 4:
                return date(int(partes[0]), int(partes[1]), int(partes[2]))
            return date(int(partes[2]), int(partes[1]), int(partes[0]))
        except ValueError:
            return None
    return None


class Reserva:
    def __init__(self, fila, indice, fecha, origen, destino, nombre, localizador_entrada):
        self.fila = fila
        self.indice = indice
        self.fecha = fecha
        self.origen = (origen or "").strip()
        self.destino = (destino or "").strip()
        self.nombre_pasajero = (nombre or "").strip()
        self.localizador_entrada = (localizador_entrada or "").strip()
        self.iata = codigo_iata(self.destino)
        self.id_reserva = ""
        self.localizador = ""
        self.coincidencia = False
        self.viajeros_en_grupo = 1
        self.errores = []
        self.fichero_destino = ""

    @property
    def clave_agrupacion(self):
        return (self.iata or "??", self.fecha)

    @property
    def clave_coincidencia(self):
        return (
            normalizar_texto(self.nombre_pasajero),
            normalizar_texto(self.origen),
            normalizar_texto(self.destino),
        )

    @property
    def valida(self):
        return not self.errores

    def validar(self):
        self.errores = []
        if self.fecha is None:
            self.errores.append("fecha de reserva vacia o con formato no reconocido")
        if not self.origen:
            self.errores.append("origen vacio")
        if not self.destino:
            self.errores.append("destino vacio")
        if not self.nombre_pasajero:
            self.errores.append("nombre del pasajero vacio")
        if self.destino and self.iata is None:
            self.errores.append("destino fuera del catalogo: " + self.destino)
        return self.valida

    def asignar_identificadores(self, repeticiones):
        base = "|".join(
            [
                self.fecha.isoformat() if self.fecha else "sin-fecha",
                normalizar_texto(self.origen),
                normalizar_texto(self.destino),
                normalizar_texto(self.nombre_pasajero),
            ]
        )
        clave = base + "|" + str(repeticiones)
        self.id_reserva = "RES-" + _hash_corto(clave, 10)

    def como_diccionario(self):
        return {
            "id_reserva": self.id_reserva,
            "fecha_reserva": self.fecha.isoformat() if self.fecha else "",
            "destino": self.destino,
            "destino_iata": self.iata or "",
            "origen": self.origen,
            "nombre_pasajero": self.nombre_pasajero,
            "localizador": self.localizador,
            "coincidencia": "SI" if self.coincidencia else "NO",
            "viajero_en_grupo": self.viajeros_en_grupo,
        }

    def __repr__(self):
        return "<Reserva {0} {1} {2} -> {3}>".format(
            self.id_reserva, self.nombre_pasajero, self.origen, self.destino
        )


def generar_localizador_grupo(reservas):
    clave = "|".join(
        [
            normalizar_texto(reservas[0].nombre_pasajero),
            normalizar_texto(reservas[0].origen),
            normalizar_texto(reservas[0].destino),
        ]
    )
    return "LOC-" + _slug(clave, 6) + "-" + _hash_corto(clave, 4)


def resolver_localizadores(reservas):
    grupos = {}
    for reserva in reservas:
        if not reserva.valida:
            continue
        grupos.setdefault(reserva.clave_coincidencia, []).append(reserva)
    for clave, miembros in grupos.items():
        if len(miembros) < 2:
            continue
        localizador = generar_localizador_grupo(miembros)
        for reserva in miembros:
            reserva.coincidencia = True
            reserva.localizador = localizador
            reserva.viajeros_en_grupo = len(miembros)
    return grupos
