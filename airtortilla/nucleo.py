import csv
import hashlib
import io
import os
import re
import sys
import unicodedata
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALFABETO = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CAMPOS = ["id_reserva", "fecha_reserva", "destino", "destino_iata", "origen", "nombre_pasajero", "localizador", "coincidencia", "viajero_en_grupo"]
FORMATOS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y")
ALIAS = {"FECHA": "fecha", "FECHA RESERVA": "fecha", "FECHA DE LA RESERVA": "fecha", "ORIGEN": "origen", "PAIS ORIGEN": "origen", "DESTINO": "destino", "PAIS DESTINO": "destino", "NOMBRE": "nombre", "NOMBRE PASAJERO": "nombre", "NOMBRE DEL PASAJERO": "nombre", "PASAJERO": "nombre", "LOCALIZADOR": "localizador"}
PAISES = dict(par.split("=") for par in "AFGANISTAN=AF;ALEMANIA=DE;ALBANIA=AL;ALGERIA=DZ;ANGOLA=AO;ANTIGUA Y BARBUDA=AG;ARABIA SAUDITA=SA;ARGENTINA=AR;ARMENIA=AM;ARUBA=AW;AUSTRALIA=AU;AUSTRIA=AT;AZERBAIYAN=AZ;BAHAMAS=BS;BAHREIN=BH;BANGLADESH=BD;BARBADOS=BB;BELARUS=BY;BELGICA=BE;BELICE=BZ;BENIN=BJ;BOLIVIA=BO;BOSNIA Y HERZEGOVINA=BA;BOTSWANA=BW;BRASIL=BR;BRUNEI=BN;BULGARIA=BG;BURKINA FASO=BF;BURUNDI=BI;CABO VERDE=CV;CAMBOYA=KH;CAMERUN=CM;CANADA=CA;CATAR=QA;CHAD=TD;CHILE=CL;CHINA=CN;CHIPRE=CY;COLOMBIA=CO;COMORAS=KM;CONGO=CG;CONGO REPUBLICA DEMOCRATICA=CD;COREA DEL NORTE=KP;COREA DEL SUR=KR;COSTA DE MARFIL=CI;COSTA RICA=CR;CROACIA=HR;CUBA=CU;DINAMARCA=DK;DJIBOUTI=DJ;DOMINICA=DM;ECUADOR=EC;EGIPTO=EG;EL SALVADOR=SV;EMIRATOS ARABES UNIDOS=AE;ESLOVENIA=SI;ESPANA=ES;ESTADOS UNIDOS=US;ESTONIA=EE;ETIOPIA=ET;FILIPINAS=PH;FINLANDIA=FI;FRANCIA=FR;GABON=GA;GAMBIA=GM;GEORGIA=GE;GHANA=GH;GRECIA=GR;GUATEMALA=GT;GUINEA=GN;GUINEA ECUATORIAL=GQ;GUYANA=GY;HAITI=HT;HONDURAS=HN;HONG KONG=HK;HUNGRIA=HU;INDIA=IN;INDONESIA=ID;IRAK=IQ;IRAN=IR;IRLANDA=IE;ISLANDIA=IS;ISLAS BAHAMAS=BH;ISRAEL=IL;ITALIA=IT;JAMAICA=JM;JAPON=JP;JORDANIA=JO;KAZAJSTAN=KZ;KENIA=KE;KIRGUISTAN=KG;KOSOVO=XK;KUBAIT=KW;LAOS=LA;LESOTO=LS;LETONIA=LV;LIBANO=LB;LIBERIA=LR;LIBIA=LY;LITUANIA=LT;LUXEMBURGO=LU;MACAO=MO;MACEDONIA DEL NORTE=MK;MADAGASCAR=MG;MALASIA=MY;MALAWI=MW;MALDIVAS=MV;MALI=ML;MALTA=MT;MARRUECOS=MA;MAURICIO=MU;MAURITANIA=MR;MEXICO=MX;MICRONESIA=FM;MOLDAVIA=MD;MONGOLIA=MN;MONTENEGRO=ME;MOZAMBIQUE=MZ;NAMIBIA=NA;NEPAL=NP;NICARAGUA=NI;NIGER=NE;NIGERIA=NG;NORUEGA=NO;NUEVA ZELANDA=NZ;PAISES BAJOS=NL;PAKISTAN=PK;PALAU=PW;PANAMA=PA;PAPUA NUEVA GUINEA=PG;PARAGUAY=PY;PERU=PE;POLONIA=PL;PORTUGAL=PT;REINO UNIDO=GB;REPUBLICA CENTROAFRICANA=CF;REPUBLICA CHECA=CZ;REPUBLICA DEMOCRATICA DEL CONGO=CD;REPUBLICA DOMINICANA=DO;REPUBLICA ESLOVACA=SK;RUSIA=RU;SALOMON=SB;SAN MARINO=SM;SAN VICENTE Y LAS GRANADINAS=VC;SANTO TOME Y PRINCIPE=ST;SENEGAL=SN;SERBIA=RS;SEYCHELLES=SC;SIERRA LEONA=SL;SINGAPUR=SG;SIRIA=SY;SOMALIA=SO;SUDAN=SD;SUECIA=SE;SUIZA=CH;TAILANDIA=TH;TANZANIA=TZ;TOGO=TG;TONGA=TO;TRINIDAD Y TOBAGO=TT;TUNEZ=TN;TURQUIA=TR;UCRANIA=UA;UGANDA=UG;URUGUAY=UY;UZBEKISTAN=UZ;VENEZUELA=VE;VIETNAM=VN;YEMEN=YE;ZAMBIA=ZM;ZIMBABUE=ZW".split(";"))
SINONIMOS = dict(par.split("=") for par in "ANDORRA=ESPANA;CATALUNA=ESPANA;DOMINICANA=REPUBLICA DOMINICANA;EEUU=ESTADOS UNIDOS;GB=REINO UNIDO;HOLANDA=PAISES BAJOS;INGLATERRA=REINO UNIDO;REP DOMINICANA=REPUBLICA DOMINICANA;REP. DOMINICANA=REPUBLICA DOMINICANA;UK=REINO UNIDO;US=ESTADOS UNIDOS;USA=ESTADOS UNIDOS".split(";"))

EJEMPLO = """fecha_reserva;origen;destino;nombre_pasajero;localizador
2026-10-02;ESPANA;FRANCIA;LUCIA MORENO;
2026-10-02;ESPANA;FRANCIA;MARCOS RUIZ;
2026-10-02;ITALIA;FRANCIA;MARCOS RUIZ;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;FRANCIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;PORTUGAL;BRASIL;JOAO SILVA;
2026-10-02;PORTUGAL;BRASIL;JOAO SILVA;
2026-10-03;ESPANA;ESTADOS UNIDOS;MARIA LOPEZ;
2026-10-03;ESPANA;ESTADOS UNIDOS;CARLOS GOMEZ;
2026-10-03;REINO UNIDO;ESTADOS UNIDOS;PETER BROWN;
2026-10-03;ESPANA;JAPON;MARTA GARCIA;
2026-10-03;MEXICO;ESPANA;DIEGO FERNANDEZ;
2026-10-03;MEXICO;ESPANA;DIEGO FERNANDEZ;
2026-10-04;ALEMANIA;ITALIA;HANNA WEBER;
2026-10-04;FRANCIA;ESPANA;JULIE MARTIN;
2026-10-04;FRANCIA;ESPANA;PIERRE DUPONT;
2026-10-04;CHINA;ESPANA;LI WEI;
2026-10-05;NORUEGA;ISLANDIA;OLAV NILSEN;
2026-10-05;NORUEGA;ISLANDIA;OLAV NILSEN;
2026-10-05;SUECIA;ISLANDIA;EVA LIND;
2026-10-05;ARGENTINA;URUGUAY;LUCIA PAZ;
2026-10-06;INDIA;EMIRATOS ARABES UNIDOS;RAJ PATEL;
2026-10-06;INDIA;EMIRATOS ARABES UNIDOS;RAJ PATEL;
2026-10-06;AUSTRALIA;NUEVA ZELANDA;JACK MURPHY;
2026-10-07;BELGICA;PAISES BAJOS;JAN PEETERS;
2026-10-07;SUIZA;PAISES BAJOS;CLAUDE WEBER;
2026-10-07;PERU;CHILE;ANA TORRES;
2026-10-07;PERU;CHILE;ANA TORRES;
2026-10-08;TURQUIA;GRECIA;MEHMET YILMAZ;
2026-10-08;CANADA;MARRUECOS;SARAH TREMBLAY;
2026-10-08;RUSIA;FINLANDIA;IVAN VOLKOV;
2026-10-09;ESPANA;CUBA;ANA MORALES;
2026-10-09;REP DOMINICANA;CUBA;PEDRO RAMIREZ;
2026-10-09;VENEZUELA;COLOMBIA;ANA MORALES;
2026-10-09;ECUADOR;COLOMBIA;DIEGO PAZ;
2026-10-10;IRLANDA;REINO UNIDO;SEAN KELLY;
2026-10-10;IRLANDA;REINO UNIDO;SEAN KELLY;
2026-10-10;ISLAS BAHAMAS;PANAMA;JOHN SMITH;
2026-10-10;SENEGAL;MARRUECOS;AMADOU DIALLO;
2026-10-11;UCRANIA;POLONIA;OLEKSANDR PETRENKO;
2026-10-11;RUMANIA;HUNGRIA;ION POPESCU;
2026-10-11;GRECIA;CHIPRE;YANNIS NIKOLOU;
2026-10-11;KAZAJSTAN;UZBEKISTAN;ALEXEY VOLKOV;
2026-10-12;THAILANDIA;JAPON;SOMCHAI PONG;
2026-10-12;AUSTRALIA;JAPON;EMILY CLARKE;
2026-10-12;COLOMBIA;PERU;CARLOS RAMOS;
2026-10-13;ESPANA;NARNIA;PABLO GARRIDO;
2026-10-13;ESPANA;ESPANA;;
"""


def normalizar(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "").replace("\ufeff", "").strip())
    return " ".join("".join(c for c in texto if not unicodedata.combining(c)).upper().split())


def codigo_iata(destino):
    clave = normalizar(destino)
    clave = SINONIMOS.get(clave, clave)
    if len(clave) == 2 and clave in set(PAISES.values()):
        return clave
    return PAISES.get(clave)


def nombre_pais(codigo):
    for pais, valor in PAISES.items():
        if valor == codigo:
            return pais
    return codigo


def parsear_fecha(valor):
    for formato in FORMATOS:
        try:
            return datetime.strptime(str(valor or "").strip(), formato).date()
        except ValueError:
            pass
    return None


def hash_corto(texto, cantidad):
    digest = hashlib.sha1(texto.encode("utf-8")).digest()
    numero = int.from_bytes(digest[:12], "big")
    salida = ""
    for _ in range(cantidad):
        numero, resto = divmod(numero, len(ALFABETO))
        salida += ALFABETO[resto]
    return salida


def slug(texto, cantidad):
    limpio = re.sub(r"[^A-Z0-9]+", "", normalizar(texto))
    return limpio[:cantidad] if limpio else "X"


def leer_texto(ruta):
    with open(ruta, "rb") as manejador:
        bruto = manejador.read()
    if bruto.startswith(b"\xef\xbb\xbf"):
        bruto = bruto[3:]
    for codificacion in ("utf-8", "cp1252"):
        try:
            return bruto.decode(codificacion)
        except UnicodeDecodeError:
            pass
    return bruto.decode("latin-1")


def detectar_delimitador(texto):
    lineas = [linea for linea in texto.splitlines()[:25] if linea.strip()]
    return max((";", ",", "\t", "|"), key=lambda sep: sum(linea.count(sep) for linea in lineas))


def leer_reservas(entrada, es_texto=False):
    texto = entrada if es_texto else leer_texto(entrada)
    if not texto.strip():
        return []
    filas = [fila for fila in csv.reader(io.StringIO(texto), delimiter=detectar_delimitador(texto)) if any(celda.strip() for celda in fila)]
    if not filas:
        return []
    mapa = {}
    for posicion, bruto in enumerate(filas[0]):
        clave = normalizar(bruto.replace("_", " "))
        if clave in ALIAS:
            mapa[ALIAS[clave]] = posicion
    if not mapa:
        mapa = {"fecha": 0, "origen": 1, "destino": 2, "nombre": 3, "localizador": 4}
    reservas = []
    veces = {}
    for indice, fila in enumerate(filas[1:]):

        def campo(nombre):
            posicion = mapa.get(nombre)
            return fila[posicion].strip() if posicion is not None and posicion < len(fila) else ""

        reserva = {
            "fila": indice + 2,
            "fecha": parsear_fecha(campo("fecha")),
            "origen": campo("origen"),
            "destino": campo("destino"),
            "nombre": campo("nombre"),
            "iata": codigo_iata(campo("destino")),
            "localizador": campo("localizador").upper(),
            "coincidencia": False,
            "viajeros": 1,
            "errores": [],
        }
        base = "|".join([reserva["fecha"].isoformat() if reserva["fecha"] else "sin-fecha", normalizar(reserva["origen"]), normalizar(reserva["destino"]), normalizar(reserva["nombre"])])
        veces[base] = veces.get(base, 0)
        reserva["id_reserva"] = "RES-" + hash_corto(base + "|" + str(veces[base]), 10)
        veces[base] += 1
        if not reserva["fecha"]:
            reserva["errores"].append("fecha de reserva vacia o con formato no reconocido")
        if not reserva["origen"]:
            reserva["errores"].append("origen vacio")
        if not reserva["destino"]:
            reserva["errores"].append("destino vacio")
        if not reserva["nombre"]:
            reserva["errores"].append("nombre del pasajero vacio")
        if reserva["destino"] and reserva["iata"] is None:
            reserva["errores"].append("destino fuera del catalogo: " + reserva["destino"])
        reservas.append(reserva)
    return reservas


def resolver_localizadores(reservas):
    grupos = {}
    for reserva in reservas:
        if not reserva["errores"]:
            clave = (normalizar(reserva["nombre"]), normalizar(reserva["origen"]), normalizar(reserva["destino"]))
            grupos.setdefault(clave, []).append(reserva)
    for miembros in grupos.values():
        if len(miembros) < 2:
            continue
        primero = miembros[0]
        clave = "|".join([normalizar(primero["nombre"]), normalizar(primero["origen"]), normalizar(primero["destino"])])
        localizador = "LOC-" + slug(clave, 6) + "-" + hash_corto(clave, 4)
        for reserva in miembros:
            reserva["coincidencia"] = True
            reserva["localizador"] = localizador
            reserva["viajeros"] = len(miembros)


def nombre_fichero(codigo, fecha):
    return "AirTortilla_{0}_{1:04d}_{2:02d}_{3:02d}".format(codigo, fecha.year, fecha.month, fecha.day)


def escribir_fichero(ruta, registros):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=CAMPOS, delimiter=";")
        escritor.writeheader()
        for reserva in registros:
            escritor.writerow({
                "id_reserva": reserva["id_reserva"],
                "fecha_reserva": reserva["fecha"].isoformat(),
                "destino": reserva["destino"],
                "destino_iata": reserva["iata"],
                "origen": reserva["origen"],
                "nombre_pasajero": reserva["nombre"],
                "localizador": reserva["localizador"],
                "coincidencia": "SI" if reserva["coincidencia"] else "NO",
                "viajero_en_grupo": reserva["viajeros"],
            })


def reiniciar(directorio):
    if not os.path.isdir(directorio):
        os.makedirs(directorio)
        return 0
    borrados = 0
    for nombre in os.listdir(directorio):
        if nombre.startswith("AirTortilla") and nombre.endswith(".csv"):
            os.remove(os.path.join(directorio, nombre))
            borrados += 1
    return borrados


def procesar(entrada, salida, es_texto=False, linea=None):
    reservas = leer_reservas(entrada, es_texto)
    if linea:
        seleccionadas = [r for r in reservas if r["fila"] == linea]
        previas = [r for r in reservas if r["fila"] < linea and not r["errores"]]
    else:
        seleccionadas = list(reservas)
        previas = []
    resolver_localizadores(previas + [r for r in seleccionadas if not r["errores"]])
    grupos = {}
    descartadas = []
    for reserva in seleccionadas:
        if reserva["errores"]:
            descartadas.append(reserva)
        else:
            grupos.setdefault(reserva["iata"] + "|" + reserva["fecha"].isoformat(), []).append(reserva)
    log = []
    ficheros = []
    for clave in sorted(grupos):
        miembros = grupos[clave]
        nombre = nombre_fichero(miembros[0]["iata"], miembros[0]["fecha"])
        registros = [r for r in previas if nombre_fichero(r["iata"], r["fecha"]) == nombre] + miembros
        for reserva in miembros:
            reserva["fichero"] = nombre
        ruta = os.path.join(salida, nombre + ".csv")
        escribir_fichero(ruta, registros)
        pais = nombre_pais(miembros[0]["iata"])
        ficheros.append({"nombre": nombre + ".csv", "ruta": ruta, "iata": miembros[0]["iata"], "pais": pais})
        log.append("Grupo {0} ({1}) -> {2}.csv con {3} reserva(s)".format(miembros[0]["iata"], pais, nombre, len(registros)))
    for reserva in descartadas:
        log.append("Linea {0} descartada, no genera fichero: {1}".format(reserva["fila"], "; ".join(reserva["errores"])))
    validas = [r for r in seleccionadas if not r["errores"]]
    informe = {
        "leidas": len(seleccionadas),
        "validas": len(validas),
        "con_localizador": len([r for r in validas if r["coincidencia"]]),
        "descartadas": len(seleccionadas) - len(validas),
    }
    return {"log": log, "ficheros": ficheros, "reservas": reservas, "informe": informe, "descartadas": descartadas}


def crear_csv_ejemplo(ruta):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as manejador:
        manejador.write(EJEMPLO)
    return ruta


def lanzar_web(puerto=8000):

    class Manejador(BaseHTTPRequestHandler):

        def do_GET(self):
            with open(os.path.join(RAIZ, "index.html"), "rb") as manejador:
                cuerpo = manejador.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *argumentos):
            pass

    print("Interfaz web en http://127.0.0.1:{0}".format(puerto))
    HTTPServer(("127.0.0.1", puerto), Manejador).serve_forever()


def main(argumentos=None):
    argumentos = sys.argv[1:] if argumentos is None else list(argumentos)
    comando = "generar"
    entrada = ""
    salida = os.path.join(RAIZ, "data", "salida")
    linea = 0
    puerto = 8000
    posicion = 0
    while posicion < len(argumentos):
        actual = argumentos[posicion]
        if actual in ("-f", "-s", "-l", "--linea", "-p", "--puerto"):
            posicion += 1
            valor = argumentos[posicion]
            if actual == "-f":
                entrada = valor
            elif actual == "-s":
                salida = valor
            elif actual in ("-l", "--linea"):
                linea = int(valor)
            else:
                puerto = int(valor)
        elif actual in ("generar", "web", "ejemplo"):
            comando = actual
        posicion += 1
    if comando == "web":
        lanzar_web(puerto)
        return 0
    if comando == "ejemplo":
        print(crear_csv_ejemplo(entrada or os.path.join(RAIZ, "data", "reservas_entrada.csv")))
        return 0
    reiniciar(salida)
    if entrada:
        resultado = procesar(entrada, salida, linea=linea or None)
        origen = entrada
    else:
        resultado = procesar(EJEMPLO, salida, es_texto=True, linea=linea or None)
        origen = "CSV de ejemplo"
    print("Modo: {0}".format("LINEA" if linea else "TOTAL"))
    print("Fichero de entrada: {0}".format(origen))
    print("Directorio de salida: {0}".format(os.path.abspath(salida)))
    print("")
    for texto in resultado["log"]:
        print(texto)
    print("")
    for fichero in resultado["ficheros"]:
        print("Pais {0} ({1}): {2}".format(fichero["pais"], fichero["iata"], fichero["nombre"]))
    informe = resultado["informe"]
    print("")
    print("Leidas {0} | Validas {1} | Con localizador {2} | Descartadas {3}".format(informe["leidas"], informe["validas"], informe["con_localizador"], informe["descartadas"]))
    return 0
