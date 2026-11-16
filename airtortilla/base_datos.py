"""Base de datos relacional local y auditoría de cambios."""
import getpass
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager

RUTA_BD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "airtortilla.db")
CAMPOS_RESERVA = (
    "fecha_reserva", "origen", "destino", "destino_iata", "nombre_pasajero",
    "localizador", "coincidencia", "viajero_en_grupo",
)


@contextmanager
def conectar():
    os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)
    db = sqlite3.connect(RUTA_BD, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def inicializar():
    with conectar() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            sal TEXT,
            clave_hash TEXT,
            metodo TEXT NOT NULL DEFAULT 'local',
            creado TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY,
            id_reserva TEXT NOT NULL UNIQUE,
            fecha_reserva TEXT NOT NULL,
            origen TEXT NOT NULL,
            destino TEXT NOT NULL,
            destino_iata TEXT NOT NULL,
            nombre_pasajero TEXT NOT NULL,
            localizador TEXT NOT NULL DEFAULT '',
            coincidencia INTEGER NOT NULL CHECK(coincidencia IN (0,1)),
            viajeros INTEGER NOT NULL CHECK(viajeros > 0),
            creada TEXT NOT NULL DEFAULT (datetime('now')),
            actualizada TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cambios (
            id INTEGER PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            reserva_id TEXT REFERENCES reservas(id_reserva),
            accion TEXT NOT NULL CHECK(accion IN ('RESERVA_CREADA','RESERVA_MODIFICADA','PROCESAR_CSV')),
            detalle TEXT NOT NULL,
            valores_anteriores TEXT,
            valores_nuevos TEXT,
            fecha TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_cambios_fecha ON cambios(fecha DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_cambios_usuario ON cambios(usuario_id, fecha DESC);
        CREATE INDEX IF NOT EXISTS idx_reservas_fecha_destino ON reservas(fecha_reserva,destino_iata);
        """)
        columnas = {fila["name"] for fila in db.execute("PRAGMA table_info(usuarios)")}
        if "metodo" not in columnas:
            db.execute("ALTER TABLE usuarios ADD COLUMN metodo TEXT NOT NULL DEFAULT 'password'")
        columnas = {fila["name"] for fila in db.execute("PRAGMA table_info(cambios)")}
        if "reserva_id" not in columnas:
            db.execute("ALTER TABLE cambios ADD COLUMN reserva_id TEXT")
        if "valores_anteriores" not in columnas:
            db.execute("ALTER TABLE cambios ADD COLUMN valores_anteriores TEXT")
        if "valores_nuevos" not in columnas:
            db.execute("ALTER TABLE cambios ADD COLUMN valores_nuevos TEXT")


def _usuario_local(db):
    nombre = (os.environ.get("AIRTORTILLA_USUARIO") or getpass.getuser() or "usuario_local").strip()
    nombre = nombre[:40] or "usuario_local"
    fila = db.execute("SELECT id,nombre FROM usuarios WHERE nombre=?", (nombre,)).fetchone()
    if fila:
        return dict(fila)
    # Cuenta local identificada por el usuario de Windows/macOS/Linux que ejecuta el servidor.
    sal = secrets.token_hex(16)
    huella = hashlib.pbkdf2_hmac("sha256", secrets.token_bytes(32), bytes.fromhex(sal), 200000).hex()
    try:
        cur = db.execute(
            "INSERT INTO usuarios(nombre,sal,clave_hash,metodo) VALUES(?,?,?,'sistema')",
            (nombre, sal, huella),
        )
        return {"id": cur.lastrowid, "nombre": nombre}
    except sqlite3.IntegrityError:
        fila = db.execute("SELECT id,nombre FROM usuarios WHERE nombre=?", (nombre,)).fetchone()
        return dict(fila)


def usuario_local():
    with conectar() as db:
        return _usuario_local(db)


def crear_usuario(nombre, clave):
    nombre = (nombre or "").strip()
    if len(nombre) < 2 or len(nombre) > 40:
        raise ValueError("El nombre debe tener entre 2 y 40 caracteres")
    if len(clave or "") < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), 200000).hex()
    with conectar() as db:
        existente = db.execute("SELECT id,metodo FROM usuarios WHERE nombre=?", (nombre,)).fetchone()
        if existente and existente["metodo"] == "sistema":
            db.execute("UPDATE usuarios SET sal=?,clave_hash=?,metodo='password' WHERE id=?",
                       (sal, digest, existente["id"]))
            return {"id": existente["id"], "nombre": nombre}
        cur = db.execute("INSERT INTO usuarios(nombre,sal,clave_hash,metodo) VALUES(?,?,?,'password')",
                         (nombre, sal, digest))
        return {"id": cur.lastrowid, "nombre": nombre}


def autenticar(nombre, clave):
    with conectar() as db:
        fila = db.execute("SELECT * FROM usuarios WHERE nombre=?", ((nombre or "").strip(),)).fetchone()
    if not fila or not fila["clave_hash"]:
        return None
    digest = hashlib.pbkdf2_hmac("sha256", (clave or "").encode("utf-8"), bytes.fromhex(fila["sal"]), 200000).hex()
    if not hmac.compare_digest(digest, fila["clave_hash"]):
        return None
    return {"id": fila["id"], "nombre": fila["nombre"]}


def _snapshot(reserva):
    return {campo: reserva[campo] for campo in CAMPOS_RESERVA}


def registrar_proceso(nombre_archivo, modo, reservas, usuario_id=None, descartadas_extra=0):
    """Guarda las reservas válidas y audita altas, cambios y ejecución en una transacción."""
    validas = [r for r in reservas if r.get("id_reserva") and r.get("fecha_reserva")]
    with conectar() as db:
        if usuario_id is None:
            usuario = _usuario_local(db)
        else:
            fila_usuario = db.execute("SELECT id,nombre FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
            if not fila_usuario:
                raise ValueError("El usuario de la sesión no existe")
            usuario = dict(fila_usuario)
        altas = 0
        modificaciones = 0
        for nueva in validas:
            rid = str(nueva["id_reserva"])
            anterior = db.execute("SELECT * FROM reservas WHERE id_reserva=?", (rid,)).fetchone()
            campos = {
                "fecha_reserva": str(nueva["fecha_reserva"]),
                "origen": str(nueva.get("origen", "")),
                "destino": str(nueva.get("destino", "")),
                "destino_iata": str(nueva.get("destino_iata", "")),
                "nombre_pasajero": str(nueva.get("nombre_pasajero", "")),
                "localizador": str(nueva.get("localizador", "")),
                "coincidencia": int(nueva.get("coincidencia") is True or
                                     str(nueva.get("coincidencia", "")).strip().upper() in ("SI", "SÍ", "TRUE", "1")),
                "viajeros": int(nueva.get("viajero_en_grupo", 1)),
            }
            if not anterior:
                db.execute("""INSERT INTO reservas(id_reserva,fecha_reserva,origen,destino,destino_iata,
                    nombre_pasajero,localizador,coincidencia,viajeros)
                    VALUES(:id_reserva,:fecha_reserva,:origen,:destino,:destino_iata,
                    :nombre_pasajero,:localizador,:coincidencia,:viajeros)""",
                    dict(id_reserva=rid, **campos))
                db.execute("""INSERT INTO cambios(usuario_id,reserva_id,accion,detalle,valores_nuevos)
                    VALUES(?,?, 'RESERVA_CREADA', ?, ?)""",
                    (usuario["id"], rid, "Se añadió la reserva {}".format(rid),
                     json.dumps(campos, ensure_ascii=False, sort_keys=True)))
                altas += 1
            else:
                viejo = {k: anterior[k] for k in campos}
                if viejo != campos:
                    db.execute("""UPDATE reservas SET fecha_reserva=:fecha_reserva,origen=:origen,
                        destino=:destino,destino_iata=:destino_iata,nombre_pasajero=:nombre_pasajero,
                        localizador=:localizador,coincidencia=:coincidencia,viajeros=:viajeros,
                        actualizada=datetime('now') WHERE id_reserva=:id_reserva""",
                        dict(id_reserva=rid, **campos))
                    db.execute("""INSERT INTO cambios(usuario_id,reserva_id,accion,detalle,
                        valores_anteriores,valores_nuevos) VALUES(?,?, 'RESERVA_MODIFICADA', ?, ?, ?)""",
                        (usuario["id"], rid, "Se modificó la reserva {}".format(rid),
                         json.dumps(viejo, ensure_ascii=False, sort_keys=True),
                         json.dumps(campos, ensure_ascii=False, sort_keys=True)))
                    modificaciones += 1
        descartadas = len(reservas) - len(validas) + max(0, int(descartadas_extra))
        detalle = "{}; modalidad {}; {} altas, {} modificaciones y {} descartadas".format(
            os.path.basename((nombre_archivo or "CSV pegado")[:200]), modo,
            altas, modificaciones, descartadas)
        db.execute("""INSERT INTO cambios(usuario_id,accion,detalle,valores_nuevos)
            VALUES(?,'PROCESAR_CSV',?,?)""",
            (usuario["id"], detalle, json.dumps(
                {"reservas_validas": len(validas), "altas": altas,
                 "modificaciones": modificaciones, "descartadas": descartadas},
                ensure_ascii=False, sort_keys=True)))
    return {"usuario": usuario["nombre"], "altas": altas, "modificaciones": modificaciones}


def listar_cambios(limite=100):
    with conectar() as db:
        return [dict(r) for r in db.execute("""
            SELECT c.id,u.nombre AS usuario,c.reserva_id,c.accion,c.detalle,
                   c.valores_anteriores,c.valores_nuevos,c.fecha
            FROM cambios c JOIN usuarios u ON u.id=c.usuario_id
            ORDER BY c.id DESC LIMIT ?
        """, (max(1, min(int(limite), 500)),))]


inicializar()
