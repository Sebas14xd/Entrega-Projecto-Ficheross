"""Persistencia local de usuarios, reservas procesadas e historial."""
import hashlib
import hmac
import os
import secrets
import sqlite3

RUTA_BD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "airtortilla.db")


def conectar():
    os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar():
    with conectar() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE,
            sal TEXT NOT NULL, clave_hash TEXT NOT NULL,
            creado TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY, id_reserva TEXT NOT NULL UNIQUE,
            fecha_reserva TEXT NOT NULL, origen TEXT NOT NULL, destino TEXT NOT NULL,
            destino_iata TEXT NOT NULL, nombre_pasajero TEXT NOT NULL,
            localizador TEXT NOT NULL DEFAULT '', coincidencia INTEGER NOT NULL,
            viajeros INTEGER NOT NULL, usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            actualizada TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cambios (
            id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            accion TEXT NOT NULL, detalle TEXT NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_cambios_fecha ON cambios(fecha);
        """)


def crear_usuario(nombre, clave):
    nombre = (nombre or "").strip()
    if len(nombre) < 2 or len(nombre) > 40:
        raise ValueError("El nombre debe tener entre 2 y 40 caracteres")
    if len(clave or "") < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), 200000).hex()
    with conectar() as db:
        cur = db.execute("INSERT INTO usuarios(nombre,sal,clave_hash) VALUES(?,?,?)", (nombre, sal, digest))
        return {"id": cur.lastrowid, "nombre": nombre}


def autenticar(nombre, clave):
    with conectar() as db:
        fila = db.execute("SELECT * FROM usuarios WHERE nombre = ?", ((nombre or "").strip(),)).fetchone()
    if not fila:
        return None
    digest = hashlib.pbkdf2_hmac("sha256", (clave or "").encode("utf-8"), bytes.fromhex(fila["sal"]), 200000).hex()
    if not hmac.compare_digest(digest, fila["clave_hash"]):
        return None
    return {"id": fila["id"], "nombre": fila["nombre"]}


def registrar_proceso(usuario_id, nombre_archivo, modo, reservas):
    validas = [r for r in reservas if not r["errores"]]
    with conectar() as db:
        for r in validas:
            db.execute("""
                INSERT INTO reservas(id_reserva,fecha_reserva,origen,destino,destino_iata,
                    nombre_pasajero,localizador,coincidencia,viajeros,usuario_id)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id_reserva) DO UPDATE SET
                    fecha_reserva=excluded.fecha_reserva, origen=excluded.origen,
                    destino=excluded.destino, destino_iata=excluded.destino_iata,
                    nombre_pasajero=excluded.nombre_pasajero, localizador=excluded.localizador,
                    coincidencia=excluded.coincidencia, viajeros=excluded.viajeros,
                    usuario_id=excluded.usuario_id, actualizada=datetime('now')
            """, (r["id_reserva"], r["fecha"].isoformat(), r["origen"], r["destino"], r["iata"],
                  r["nombre"], r["localizador"], int(r["coincidencia"]), r["viajeros"], usuario_id))
        db.execute("INSERT INTO cambios(usuario_id,accion,detalle) VALUES(?,?,?)",
                   (usuario_id, "PROCESAR_CSV",
                    "{}: modalidad {}, {} reservas guardadas, {} descartadas".format(
                        os.path.basename(nombre_archivo or "CSV pegado"), modo, len(validas),
                        len(reservas) - len(validas))))


def listar_cambios(limite=100):
    with conectar() as db:
        return [dict(r) for r in db.execute("""
            SELECT c.id,u.nombre AS usuario,c.accion,c.detalle,c.fecha
            FROM cambios c JOIN usuarios u ON u.id=c.usuario_id
            ORDER BY c.id DESC LIMIT ?
        """, (limite,))]


inicializar()
