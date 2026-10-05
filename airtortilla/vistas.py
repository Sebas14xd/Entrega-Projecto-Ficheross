ESTILO = """
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", Tahoma, sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 15px;
}
.envoltorio { max-width: 1180px; margin: 0 auto; padding: 24px 18px 60px; }
.cabecera {
  background: linear-gradient(120deg, #0ea5e9, #22c55e);
  color: #05283d;
  padding: 22px 26px;
  border-radius: 14px;
  margin-bottom: 20px;
}
.cabecera h1 { margin: 0 0 6px 0; font-size: 26px; letter-spacing: 0.5px; }
.cabecera p { margin: 0; font-size: 14px; }
.panel {
  background: #111c33;
  border: 1px solid #24324f;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 18px;
}
.panel h2 { margin: 0 0 14px 0; font-size: 18px; color: #7dd3fc; }
.panel h3 { margin: 16px 0 8px 0; font-size: 15px; color: #a7f3d0; }
label { display: block; margin: 10px 0 4px 0; font-size: 13px; color: #94a3b8; }
input[type=text], input[type=number], select, textarea {
  width: 100%;
  padding: 9px 10px;
  background: #0b1426;
  border: 1px solid #2c3b5c;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 14px;
}
input[type=file] { color: #cbd5e1; }
.fila { display: flex; gap: 16px; flex-wrap: wrap; }
.columna { flex: 1 1 240px; }
.opciones { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.opcion {
  border: 2px solid #2c3b5c;
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
  background: #0b1426;
  min-width: 210px;
}
.opcion.seleccionada { border-color: #22c55e; background: #0f2a1c; }
.opcion strong { display: block; color: #e2e8f0; }
.opcion span { font-size: 12px; color: #94a3b8; }
.boton {
  background: #22c55e;
  color: #04240f;
  border: 0;
  padding: 11px 20px;
  border-radius: 9px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 16px;
}
.boton.secundario { background: #334155; color: #e2e8f0; }
.boton.azul { background: #0ea5e9; color: #04283d; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }
th, td {
  text-align: left;
  padding: 8px 9px;
  border-bottom: 1px solid #223049;
  vertical-align: top;
}
th { color: #7dd3fc; font-weight: 600; }
.tarjetas { display: flex; gap: 12px; flex-wrap: wrap; }
.tarjeta {
  background: #0b1426;
  border: 1px solid #24324f;
  border-radius: 10px;
  padding: 12px 16px;
  min-width: 130px;
}
.tarjeta .valor { font-size: 24px; font-weight: 700; color: #22c55e; }
.tarjeta .etiqueta { font-size: 12px; color: #94a3b8; }
.etiqueta-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
}
.ok { background: #14532d; color: #bbf7d0; }
.coincidencia { background: #7c2d12; color: #fed7aa; }
.error { background: #7f1d1d; color: #fecaca; }
.linea-log {
  font-family: Consolas, monospace;
  font-size: 12.5px;
  padding: 6px 8px;
  border-left: 3px solid #2c3b5c;
  margin-bottom: 4px;
  background: #0b1426;
  border-radius: 0 6px 6px 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.linea-log.OK { border-left-color: #22c55e; }
.linea-log.COINCIDENCIA { border-left-color: #f59e0b; }
.linea-log.ERROR { border-left-color: #ef4444; color: #fecaca; }
a { color: #38bdf8; }
a.boton-enlace {
  text-decoration: none;
  display: inline-block;
  padding: 5px 11px;
  border-radius: 7px;
  background: #1e293b;
  font-size: 12.5px;
  border: 1px solid #334155;
}
a.boton-enlace:hover { background: #334155; }
.aviso {
  background: #422006;
  border: 1px solid #a16207;
  color: #fde68a;
  padding: 11px 14px;
  border-radius: 9px;
  margin-bottom: 14px;
  font-size: 13.5px;
}
.ok-aviso { background: #052e16; border-color: #16a34a; color: #bbf7d0; }
pre.previsualizacion {
  background: #020617;
  border: 1px solid #24324f;
  border-radius: 9px;
  padding: 12px;
  overflow-x: auto;
  font-size: 12px;
  max-height: 340px;
  white-space: pre;
}
.envoltorio-pre { margin-top: 10px; }
.pie { text-align: center; color: #64748b; font-size: 12.5px; margin-top: 26px; }
details summary { cursor: pointer; color: #7dd3fc; font-size: 14px; margin-bottom: 8px; }
.modo-activo { color: #22c55e; font-weight: 700; }
"""


def _escapar(valor):
    if valor is None:
        return ""
    texto = str(valor)
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return texto.replace('"', "&quot;")


def _envolver(titulo, cuerpo):
    return (
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>{0} | AirTortilla</title><style>{1}</style></head><body>"
        "<div class='envoltorio'>{2}"
        "<div class='pie'>AirTortilla - Proyecto Ficheros - Python 3 sin dependencias externas</div>"
        "</div></body></html>"
    ).format(_escapar(titulo), ESTILO, cuerpo)


def vista_indice(entradas, salida_ruta, ultima_ejecucion, mensaje=None):
    partes = []
    partes.append(_cabecera())
    if mensaje:
        clase = "ok-aviso" if mensaje.startswith("OK") else "aviso"
        partes.append("<div class='{0}'>{1}</div>".format(clase, _escapar(mensaje)))
    partes.append(
        (
            "<div class='panel'><h2>1. Selecciona el fichero de reservas de entrada</h2>"
            "<form method='post' action='/procesar' enctype='multipart/form-data'>"
            "<div class='fila'><div class='columna'>"
            "<label>Fichero CSV disponible en el servidor</label>"
            "<select name='fichero_servidor'>{0}</select>"
            "</div><div class='columna'>"
            "<label>O sube tu propio fichero CSV desde el equipo</label>"
            "<input type='file' name='fichero_subido' accept='.csv,text/csv'>"
            "</div></div>"
            "<h3>2. Elige la modalidad de ejecucion</h3>"
            "<div class='opciones'>"
            "<div class='opcion seleccionada' id='opTotal' onclick='elegir(this)'>"
            "<strong>Modalidad total</strong>"
            "<span>Procesa todas las lineas del CSV y genera los ficheros por pais de destino</span>"
            "</div>"
            "<div class='opcion' id='opLinea' onclick='elegir(this)'>"
            "<strong>Modalidad linea a linea</strong>"
            "<span>Procesa una sola linea del CSV y anade su reserva a su fichero de destino</span>"
            "</div>"
            "</div>"
            "<input type='hidden' name='modalidad' id='campoModalidad' value='TOTAL'>"
            "<div class='fila'><div class='columna' style='max-width:280px'>"
            "<label>Numero de linea del CSV (la 2 es la primera reserva)</label>"
            "<input type='number' name='linea' id='campoLinea' min='2' value='2' "
            "oninput='marcarLinea()'>"
            "</div><div class='columna' style='align-self:flex-end'>"
            "<button class='boton' type='submit'>Generar y consultar ficheros</button>"
            "</div></div>"
            "</form></div>"
        ).format(_escapar(_opciones_entradas(entradas)))
    )
    partes.append(
        "<div class='panel'><h2>Resumen del ultimo proceso</h2>{0}</div>".format(
            _resumen_o_vacio(ultima_ejecucion)
        )
    )
    partes.append(_panel_ficheros(ultima_ejecucion))
    partes.append(_panel_log(ultima_ejecucion))
    partes.append(
        "<div class='panel'><h2>Zona de peligro</h2>"
        "<form method='post' action='/limpiar'>"
        "<button class='boton secundario' type='submit'>Borrar los ficheros generados</button>"
        "</form><p style='color:#64748b;font-size:12.5px'>Se eliminan unicamente los "
        "ficheros AirTortilla_*.csv de: <code>{0}</code></p></div>".format(_escapar(salida_ruta))
    )
    partes.append(
        "<script>function elegir(elegida){"
        "document.getElementById('opTotal').classList.remove('seleccionada');"
        "document.getElementById('opLinea').classList.remove('seleccionada');"
        "elegida.classList.add('seleccionada');"
        "document.getElementById('campoModalidad').value="
        "elegida.id=='opTotal'?'TOTAL':'LINEA';}"
        "function marcarLinea(){"
        "var campo=document.getElementById('campoLinea');"
        "if(campo.value>1){elegir(document.getElementById('opLinea'));}}</script>"
    )
    return _envolver("Inicio", "".join(partes))


def _cabecera():
    return (
        "<div class='cabecera'><h1>AirTortilla</h1>"
        "<p>Division automatica de reservas en ficheros independientes por pais de destino "
        "con el formato AirTortilla_XX_YYYY_MM_DD</p></div>"
    )


def _opciones_entradas(entradas):
    if not entradas:
        return "<option value=''>No hay ficheros CSV en la carpeta data</option>"
    partes = []
    for entrada in entradas:
        partes.append("<option value='{0}'>{0}</option>".format(_escapar(entrada)))
    return "".join(partes)


def _resumen_o_vacio(ejecucion):
    if not ejecucion:
        return (
            "<p style='color:#94a3b8;font-size:14px'>Todavia no se ha ejecutado ninguna "
            "generacion de ficheros.</p>"
        )
    informe = ejecucion["informe"]
    return (
        "<div class='tarjetas'>"
        "<div class='tarjeta'><div class='valor'>{0}</div><div class='etiqueta'>Lineas leidas</div></div>"
        "<div class='tarjeta'><div class='valor'>{1}</div><div class='etiqueta'>Reservas validas</div></div>"
        "<div class='tarjeta'><div class='valor'>{2}</div><div class='etiqueta'>Con localizador</div></div>"
        "<div class='tarjeta'><div class='valor'>{3}</div><div class='etiqueta'>Ficheros generados</div></div>"
        "<div class='tarjeta'><div class='valor'>{4}</div><div class='etiqueta'>Paises destino</div></div>"
        "<div class='tarjeta'><div class='valor'>{5}</div><div class='etiqueta'>Descartadas</div></div>"
        "</div>"
        "<p style='color:#94a3b8;font-size:13px;margin-top:12px'>"
        "Modo <span class='modo-activo'>{6}</span> - fichero de entrada "
        "<code>{7}</code> - generado el {8}</p>"
    ).format(
        informe["total_leidas"],
        informe["total_validas"],
        informe["total_con_localizador"],
        len(ejecucion["ficheros"]),
        len(ejecucion["resumen_paises"]),
        informe["total_invalidas"],
        ejecucion["modo"],
        _escapar(ejecucion["origen"]),
        _escapar(ejecucion["generado"]),
    )


def _solo_nombre(ruta):
    return str(ruta).replace("\\", "/").rsplit("/", 1)[-1]


def _panel_ficheros(ejecucion):
    if not ejecucion:
        return "<div class='panel'><h2>Ficheros generados por pais de destino</h2></div>"
    partes = ["<div class='panel'><h2>Ficheros generados por pais de destino</h2>"]
    partes.append("<h3>Resumen por pais</h3><table><tr><th>Pais</th><th>Codigo IATA</th>"
                  "<th>Reservas</th><th>Ficheros</th></tr>")
    for pais in ejecucion["resumen_paises"]:
        nombres = "<br>".join(
            "<a class='boton-enlace' href='/fichero/{0}'>{0}</a>".format(
                _escapar(_solo_nombre(ruta))
            )
            for ruta in pais["ficheros"]
        )
        partes.append(
            "<tr><td>{0}</td><td><strong>{1}</strong></td><td>{2}</td><td>{3}</td></tr>".format(
                _escapar(pais["pais"]), _escapar(pais["iata"]), pais["reservas"], nombres
            )
        )
    partes.append("</table>")
    partes.append("<h3>Ficheros uno a uno</h3><table><tr><th>Fichero</th><th>Pais</th>"
                  "<th>IATA</th><th>Fecha reserva</th><th>Lineas</th><th>Acciones</th></tr>")
    for item in ejecucion["ficheros"]:
        partes.append(
            "<tr><td><code>{0}</code></td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
            "<td><a class='boton-enlace' href='/fichero/{0}'>Ver</a> "
            "<a class='boton-enlace' href='/descargar/{0}'>Descargar</a></td></tr>".format(
                _escapar(item["nombre"]),
                _escapar(item["pais"]),
                _escapar(item["iata"]),
                _escapar(item["fecha"]),
                item["lineas"],
            )
        )
    partes.append("</table></div>")
    return "".join(partes)


def _panel_log(ejecucion):
    if not ejecucion:
        return "<div class='panel'><h2>Proceso paso a paso</h2></div>"
    partes = ["<div class='panel'><h2>Proceso paso a paso</h2>"]
    if ejecucion["log"]:
        partes.append("<details open><summary>Resumo de agrupacion por destino</summary>")
        for linea in ejecucion["log"]:
            partes.append("<div class='linea-log'>{0}</div>".format(_escapar(linea)))
        partes.append("</details>")
    partes.append("<details open><summary>Detalle linea a linea</summary>")
    for entrada in ejecucion["detalle"]:
        partes.append(
            "<div class='linea-log {0}'>[{1}] {2}</div>".format(
                entrada["tipo"], entrada["fila"], _escapar(entrada["texto"])
            )
        )
    partes.append("</details>")
    if ejecucion["contenido"]:
        partes.append("<h3>Vista previa del contenido</h3>")
        for nombre, texto in ejecucion["contenido"].items():
            partes.append(
                "<details><summary>{0}</summary><div class='envoltorio-pre'>"
                "<pre class='previsualizacion'>{1}</pre></div></details>".format(
                    _escapar(nombre), _escapar(texto)
                )
            )
    partes.append("</div>")
    return "".join(partes)


def vista_error(mensaje):
    cuerpo = (
        "<div class='cabecera'><h1>AirTortilla</h1><p>Error en la peticion</p></div>"
        "<div class='panel'><div class='aviso'>{0}</div>"
        "<a class='boton-enlace' href='/'>Volver al inicio</a></div>"
    ).format(_escapar(mensaje))
    return _envolver("Error", cuerpo)


def vista_fichero(nombre, contenido):
    cuerpo = (
        "<div class='panel'><h2>{0}</h2>"
        "<a class='boton-enlace' href='/descargar/{0}'>Descargar este CSV</a> "
        "<a class='boton-enlace' href='/'>Volver</a>"
        "<div class='envoltorio-pre'><pre class='previsualizacion'>{1}</pre></div></div>"
    ).format(_escapar(nombre), _escapar(contenido))
    return _envolver(nombre, cuerpo)
