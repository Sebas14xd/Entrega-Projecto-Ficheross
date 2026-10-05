"""
AirTortilla - interfaz web de reservas.

Hace tres cosas sobre un CSV de reservas:
  1. Ordena las reservas automaticamente.
  2. Detecta que pasajeros estan repetidos (mismo nombre, origen y destino).
  3. Asigna un codigo unico a cada reserva, para que los repetidos nunca
     compartan codigo.

Para verlo:
    python reservas_web.py

Se abre el navegador en http://127.0.0.1:8000. Se para con Ctrl + C.
"""

import csv
import json
import os
import random
import tempfile
import unicodedata
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

PUERTO = 8000
FICHERO_POR_DEFECTO = "reservas.csv"

# Sin I, O, 0 ni 1 porque se confunden al leerlos.
LETRAS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LARGO_CODIGO = 6
FECHAS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


def comparar(texto):
    """Sin tildes y en mayusculas, para comparar nombres iguales."""
    limpio = " ".join(str(texto or "").split()).replace("_", " ")
    descompuesto = unicodedata.normalize("NFKD", limpio)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).upper()


def leer_fecha(valor):
    """Devuelve la fecha en AAAA-MM-DD, o cadena vacia si no la entiende."""
    for formato in FECHAS:
        try:
            return datetime.strptime(str(valor or "").strip(), formato).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def leer_csv(texto):
    """Lee el CSV y devuelve (reservas, avisos)."""
    filas = [f for f in csv.reader(texto.splitlines()) if any(c.strip() for c in f)]
    if not filas:
        raise ValueError("El fichero esta vacio")

    cabeceras = [comparar(c) for c in filas[0]]

    def columna(*nombres):
        for nombre in nombres:
            for i, cabecera in enumerate(cabeceras):
                if cabecera == comparar(nombre):
                    return i
        return -1

    col_destino = columna("destino", "pais destino")
    col_origen = columna("origen", "pais origen")
    col_pasajero = columna("nombre pasajero", "nombre del pasajero", "nombre", "pasajero")
    col_fecha = columna("fecha reserva", "fecha")

    faltan = [n for n, c in (("Destino", col_destino), ("Origen", col_origen),
                             ("Nombre del Pasajero", col_pasajero)) if c == -1]
    if faltan:
        raise ValueError("Faltan estas columnas en el CSV: " + ", ".join(faltan))

    def celda(fila, indice):
        return fila[indice] if 0 <= indice < len(fila) else ""

    reservas, avisos = [], []
    for numero, fila in enumerate(filas[1:], start=2):
        pasajero = " ".join(celda(fila, col_pasajero).split())
        if not pasajero:
            avisos.append("Linea %d: descartada, sin nombre de pasajero" % numero)
            continue
        reservas.append({
            "linea": numero,
            "destino": celda(fila, col_destino).strip().upper()[:2],
            "origen": celda(fila, col_origen).strip().upper()[:2],
            "pasajero": pasajero,
            "fecha": leer_fecha(celda(fila, col_fecha)),
            "codigo": "",
            "repetido": False,
        })

    if not reservas:
        raise ValueError("No hay reservas validas en el fichero")
    return reservas, avisos


def procesar_texto(texto):
    """Procesa el contenido de un CSV y devuelve lo que ve la pagina."""
    reservas, avisos = leer_csv(texto)

    # 1. Ordenar por destino, origen, pasajero y fecha.
    #    La linea original rompe los empates, asi que el orden es siempre igual.
    reservas.sort(key=lambda r: (r["destino"], r["origen"],
                                 comparar(r["pasajero"]), r["fecha"], r["linea"]))

    # 2. Detectar pasajeros repetidos: mismo nombre, origen y destino.
    #    La fecha NO entra, porque el enunciado no la cuenta.
    grupos = {}
    for reserva in reservas:
        clave = (reserva["destino"], reserva["origen"], comparar(reserva["pasajero"]))
        grupos.setdefault(clave, []).append(reserva)

    repetidos = [reservas_grupo for reservas_grupo in grupos.values() if len(reservas_grupo) >= 2]
    repetidos.sort(key=lambda g: -len(g))

    for grupo in repetidos:
        for reserva in grupo:
            reserva["repetido"] = True

    # 3. Asignar un codigo unico a cada reserva.
    azar, usados = random.SystemRandom(), set()
    for reserva in reservas:
        while True:
            codigo = "".join(azar.choice(LETRAS) for _ in range(LARGO_CODIGO))
            if codigo not in usados:
                break
        usados.add(codigo)
        reserva["codigo"] = codigo

    return {
        "total_reservas": len(reservas),
        "total_grupos": len(repetidos),
        "total_pasajeros": sum(1 for r in reservas if r["repetido"]),
        "codigos_repetidos": len(reservas) - len(usados),
        "avisos": avisos,
        "reservas": reservas,
        "grupos": [{
            "nombre": g[0]["pasajero"],
            "origen": g[0]["origen"],
            "destino": g[0]["destino"],
            "total": len(g),
            "codigos": [r["codigo"] for r in g],
        } for g in repetidos],
    }


def procesar_fichero(ruta):
    """Procesa un CSV del disco."""
    with open(ruta, "r", encoding="utf-8-sig") as fichero:
        return procesar_texto(fichero.read())


# La pagina web: un formulario y dos tablas.
PAGINA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AirTortilla - Reservas</title>
<style>
    body { margin:0; font-family:Arial,sans-serif; background:#f4f6fa; color:#1f2937; }
    h1 { background:#0f3d6e; color:white; margin:0; padding:1.2rem; font-size:1.3rem; }
    main { max-width:1000px; margin:1.5rem auto; padding:0 1rem; }
    .caja { background:white; border:1px solid #dbe1ea; border-radius:8px;
            padding:1.2rem; margin-bottom:1.2rem; }
    h2 { font-size:1rem; color:#0f3d6e; margin:0 0 .8rem 0; }
    input[type=text] { padding:.5rem; border:1px solid #cbd5e1; border-radius:5px;
                       font-size:.9rem; width:180px; }
    button { padding:.55rem 1.2rem; background:#0f3d6e; color:white; border:0;
             border-radius:5px; font-size:.9rem; cursor:pointer; }
    button:hover { background:#1a5490; }
    button.gris { background:#64748b; }
    .numeros { display:flex; gap:.8rem; flex-wrap:wrap; }
    .num { flex:1; min-width:110px; background:#f8fafc; border:1px solid #e2e8f0;
           border-radius:6px; padding:.7rem; text-align:center; }
    .num b { display:block; font-size:1.6rem; color:#0f3d6e; }
    .num span { font-size:.72rem; color:#6b7280; }
    table { width:100%; border-collapse:collapse; font-size:.87rem; }
    th,td { padding:.5rem; text-align:left; border-bottom:1px solid #e8edf4; }
    th { background:#f8fafc; font-size:.73rem; text-transform:uppercase; color:#475569; }
    .cod { font-family:Consolas,monospace; font-weight:bold; color:#15803d; }
    .marca { background:#fef3c7; color:#92400e; font-size:.66rem;
             padding:.1rem .35rem; border-radius:3px; margin-left:.3rem; }
    .mal { background:#fef2f2; border-left:4px solid #dc2626; color:#991b1b; padding:.8rem; }
    .vacio { color:#94a3b8; font-style:italic; }
</style>
</head>
<body>
<h1>AirTortilla &mdash; Proceso de reservas</h1>
<main>

<div class="caja">
    <h2>1. Elige tu CSV</h2>
    <input type="file" id="archivo" accept=".csv,text/csv">
    <input type="text" id="nombre" value="__FICHERO__" size="18">
    <button onclick="procesar()">Procesar</button>
    <button class="gris" onclick="descargar()">Descargar</button>
</div>

<div id="salida"></div>

</main>
<script>
var ultimo = null;

// Un solo boton: si has elegido un fichero usa ese, si no usa el nombre escrito.
function procesar() {
    var caja = document.getElementById('salida');
    var archivo = document.getElementById('archivo').files[0];

    if (archivo) {
        var lector = new FileReader();
        lector.onload = function (e) { pedir({contenido: e.target.result}, archivo.name); };
        lector.onerror = function () { error('No se ha podido leer el fichero.'); };
        lector.readAsText(archivo);
        return;
    }

    var nombre = document.getElementById('nombre').value.trim();
    if (nombre) { pedir({fichero: nombre}, nombre); }
    else { error('Elige un fichero o escribe un nombre.'); }
}

function pedir(datos, nombre) {
    document.getElementById('salida').innerHTML = '<div class="caja">Procesando...</div>';

    fetch('/api/procesar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(datos)
    })
    .then(function (r) {
        return r.json().then(function (j) {
            if (!r.ok) { throw new Error(j.error); }
            j.fichero = nombre;
            pintar(j);
        });
    })
    .catch(function (e) { error(e.message); });
}

function error(texto) {
    document.getElementById('salida').innerHTML =
        '<div class="caja"><div class="mal"><b>Error:</b> ' + texto + '</div></div>';
}

function txt(v) {
    return (v === null || v === undefined) ? '' : String(v);
}

function pintar(d) {
    var h = '';

    // Resumen
    h += '<div class="caja"><h2>2. Resumen</h2><div class="numeros">';
    h += '<div class="num"><b>' + d.total_reservas + '</b><span>Reservas</span></div>';
    h += '<div class="num"><b>' + d.total_grupos + '</b><span>Grupos repetidos</span></div>';
    h += '<div class="num"><b>' + d.total_pasajeros + '</b><span>Pasajeros repetidos</span></div>';
    h += '<div class="num"><b>' + d.codigos_repetidos + '</b><span>Codigos repetidos</span></div>';
    h += '</div>';
    if (d.avisos.length) {
        h += '<p class="vacio">' + d.avisos.join('<br>') + '</p>';
    }
    h += '</div>';

    // Reservas ordenadas
    h += '<div class="caja"><h2>3. Reservas ordenadas</h2>';
    h += '<table><tr><th>Codigo</th><th>Fecha</th><th>Destino</th><th>Origen</th><th>Pasajero</th></tr>';
    for (var i = 0; i < d.reservas.length; i++) {
        var r = d.reservas[i];
        h += '<tr><td class="cod">' + txt(r.codigo)
           + (r.repetido ? '<span class="marca">repetido</span>' : '')
           + '</td><td>' + txt(r.fecha) + '</td><td>' + txt(r.destino)
           + '</td><td>' + txt(r.origen) + '</td><td>' + txt(r.pasajero) + '</td></tr>';
    }
    h += '</table></div>';

    // Pasajeros repetidos
    h += '<div class="caja"><h2>4. Pasajeros repetidos y su codigo</h2>';
    if (!d.grupos.length) {
        h += '<p class="vacio">No hay pasajeros coincidentes.</p>';
    } else {
        h += '<table><tr><th>Pasajero</th><th>Origen</th><th>Destino</th><th>Reservas</th><th>Codigos</th></tr>';
        for (var g = 0; g < d.grupos.length; g++) {
            var q = d.grupos[g];
            h += '<tr><td>' + txt(q.nombre) + '</td><td>' + txt(q.origen)
               + '</td><td>' + txt(q.destino) + '</td><td>' + q.total
               + '</td><td class="cod">' + q.codigos.join(', ') + '</td></tr>';
        }
        h += '</table>';
    }
    h += '</div>';

    ultimo = d;
    document.getElementById('salida').innerHTML = h;
}

function descargar() {
    if (!ultimo) { error('Primero procesa un fichero.'); return; }

    var csv = 'Codigo,Destino,Origen,Nombre_Pasajero,Fecha_Reserva\\n';
    for (var i = 0; i < ultimo.reservas.length; i++) {
        var r = ultimo.reservas[i];
        csv += [r.codigo, r.destino, r.origen, r.pasajero, r.fecha].join(',') + '\\n';
    }

    var enlace = document.createElement('a');
    enlace.href = URL.createObjectURL(new Blob(['\\ufeff' + csv], {type: 'text/csv;charset=utf-8'}));
    enlace.download = ultimo.fichero.replace(/\\.csv$/i, '') + '_ordenadas.csv';
    enlace.click();
}

// Al abrir la pagina, procesa el fichero por defecto.
procesar();
</script>
</body>
</html>
"""


class Manejador(BaseHTTPRequestHandler):
    """Atiende al navegador: le da la pagina y recibe los ficheros."""

    def enviar(self, cuerpo, tipo, codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        """Peticion normal: devolver la pagina."""
        self.enviar(PAGINA.replace("__FICHERO__", FICHERO_POR_DEFECTO).encode("utf-8"),
                    "text/html")

    def do_POST(self):
        """Peticion de procesar: devolver los datos en JSON."""
        largo = int(self.headers.get("Content-Length", 0))
        peticion = json.loads(self.rfile.read(largo).decode("utf-8"))
        nombre = peticion.get("fichero", FICHERO_POR_DEFECTO)

        try:
            if "contenido" in peticion:
                # Fichero subido: se guarda en uno temporal y se procesa.
                descriptor, ruta = tempfile.mkstemp(suffix=".csv")
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as fichero:
                    fichero.write(peticion["contenido"])
                try:
                    datos = procesar_fichero(ruta)
                finally:
                    os.unlink(ruta)
            else:
                datos = procesar_fichero(nombre)

            datos["fichero"] = nombre
            cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")

        except FileNotFoundError:
            self.enviar(json.dumps({"error": "No existe el fichero '%s'" % nombre}).encode("utf-8"),
                        "application/json", 400)
        except Exception as fallo:
            self.enviar(json.dumps({"error": str(fallo)}).encode("utf-8"),
                        "application/json", 400)

        else:
            self.enviar(cuerpo, "application/json")


if __name__ == "__main__":
    print("=" * 55)
    print("AirTortilla - http://%s:%d" % ("127.0.0.1", PUERTO))
    print("Fichero por defecto: %s" % FICHERO_POR_DEFECTO)
    print("Ctrl + C para parar")
    print("=" * 55)

    servidor = HTTPServer(("127.0.0.1", PUERTO), Manejador)
    webbrowser.open("http://127.0.0.1:%d" % PUERTO)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")