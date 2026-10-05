# Entrega-Projecto-Ficheross

## AirTortilla - Entrega Proyecto Ficheros

Proyecto de la entrega "Entrega Proyecto Ficheros" de AirTortilla.

## Integrantes

| Integrante | Reparto |
| ---------- | ------- |
| Marco | Catalogo de paises e IATA, entidad de reserva, identificador unico y localizador de coincidencias, interfaz web y documentacion |
| Sebas | Lectura del CSV de entrada, agrupacion por pais de destino y generacion de los ficheros AirTortilla_XX_YYYY_MM_DD, CSV de ejemplo y pruebas automaticas |

Repositorio: https://github.com/Sebas14xd/Entrega-Projecto-Ficheross rama Marco

AirTortilla necesita repartir las reservas en ficheros independientes segun el
pais de destino para poder gestionarlas y distribuirlas mejor segun la
procedencia internacional de cada reserva.

## Que hace

1 Lee un fichero CSV con la informacion de las reservas
2 Valida cada linea
3 Asigna un identificador unico a cada reserva
4 Detecta los pasajeros que coinciden en nombre, origen y destino y les asigna
  un localizador comun
5 Reparte las reservas en un fichero por pais de destino y fecha con el nombre
  AirTortilla_XX_YYYY_MM_DD
6 Muestra todo el proceso en la interfaz web, en modalidad total y linea a linea

## Stack

Python 3 con la libreria estandar. Sin dependencias externas, no hace falta
pip install. La interfaz es web y se sirve con el servidor http de la libreria
estandar.

## Como se ejecuta

Opcion A, interfaz web

```
python main.py web
```

Abre http://127.0.0.1:8000 en el navegador

Opcion B, terminal

```
python main.py generar
python main.py generar --linea 6
python main.py generar -f data/mi_fichero.csv -s data/salida
```

Pruebas

```
python -m unittest discover -s tests
```

## Estructura

```
main.py                     punto de entrada
airtortilla/paises.py       catalogo pais -> codigo IATA
airtortilla/modelos.py      entidad Reserva, identificador y localizador
airtortilla/lector_csv.py   lectura y escritura de CSV
airtortilla/procesador.py   agrupacion por pais de destino y generacion
airtortilla/vistas.py       interfaz web en HTML
airtortilla/servidor.py     servidor web y rutas
airtortilla/cli.py          comandos de terminal
airtortilla/datos_ejemplo.py  CSV de ejemplo con los casos de coincidencia
data/reservas_entrada.csv   CSV de entrada
data/salida/                ficheros generados
tests/                      pruebas automaticas
```

## Formato del CSV de entrada

Separador automatico, acepta punto y coma, coma, tabulador o barra vertical.
Los nombres de las columnas admiten tildes, espacios o guiones bajos y se
normalizan sin distinguir mayusculas.

```
fecha_reserva;origen;destino;nombre_pasajero;localizador
2026-10-02;ESPANA;FRANCIA;LUCIA MORENO;
```

Columnas obligatorias

| Columna             | Descripcion                                        |
| ------------------- | -------------------------------------------------- |
| fecha_reserva       | Fecha de realizacion de la reserva                  |
| origen              | Pais de origen del pasajero                        |
| destino             | Pais de destino de la reserva                      |
| nombre_pasajero     | Nombre completo del pasajero                       |

Columna opcional

| Columna     | Descripcion                                       |
| ----------- | ------------------------------------------------- |
| localizador | Localizador de la reserva, si ya existe           |

Formatos de fecha aceptados

```
2026-10-02
02/10/2026
02-10-2026
2026/10/02
```

## Ficheros de salida

Uno por cada combinacion de pais de destino y fecha de reserva

```
AirTortilla_FR_2026_10_02.csv
AirTortilla_JP_2026_10_02.csv
AirTortilla_ES_2026_10_04.csv
```

XX es el codigo IATA de dos signos del pais de destino, YYYY el ano, MM el mes
y DD el dia de la fecha de realizacion de la reserva

Columnas del fichero de salida

| Columna            | Descripcion                                          |
| ------------------ | ---------------------------------------------------- |
| id_reserva         | Identificador univoco e inequivoco de la reserva     |
| fecha_reserva      | Fecha de realizacion de la reserva                   |
| destino            | Pais de destino                                      |
| destino_iata       | Codigo IATA del pais de destino                      |
| origen             | Pais de origen                                       |
| nombre_pasajero    | Nombre del pasajero                                  |
| localizador        | Localizador comun si el pasajero coincide            |
| coincidencia       | SI cuando el pasajero coincide con otro              |
| viajero_en_grupo    | Numero de pasajeros del grupo de coincidencia        |

## Identificacion univoca y localizador

Cada reserva recibe un identificador RES- seguido de diez caracteres derivados
de la fecha, el origen, el destino y el nombre del pasajero mas el numero de
veces que aparece esa combinacion. Dos lineas identicas producen
identificadores distintos y siempre se puede saber a que linea del CSV de
entrada corresponde cada una

Cuando dos o mas pasajeros coinciden en nombre, origen y destino, todos reciben
el mismo localizador LOC- seguido de una abreviatura del nombre y cuatro
caracteres del grupo de coincidencia. El localizador se calcula con los datos
del grupo, asi que es estable entre ejecuciones

Ejemplo del grupo de cinco pasajeros coincidentes del fichero de ejemplo

```
LOC-ANNASC-AM18    ANNA SCHMIDT, ALEMANIA -> JAPON, 5 viajeros
```

Casos de coincidencia incluidos en data/reservas_entrada.csv

| Caso | Pasajero      | Origen  | Destino  | Viajeros |
| ---- | ------------- | ------- | -------- | -------- |
| 1    | MARCOS RUIZ   | ESPANA  | FRANCIA  | 2        |
| 2    | ANNA SCHMIDT  | ALEMANIA | JAPON   | 5        |
| 3    | JOAO SILVA    | PORTUGAL | BRASIL   | 2        |

En el caso 2 hay ademas una sexta linea con ANNA SCHMIDT pero con origen
FRANCIA, que no coincide porque el origen es distinto y por eso no lleva
localizador

## Lineas invalidas

Una linea se descarta y no genera fichero cuando le falta algun campo
obligatorio, cuando la fecha no se reconoce o cuando el pais de destino no
esta en el catalogo. La interfaz muestra el motivo de cada descarte

En el CSV de ejemplo hay dos lineas invalidas a proposito, una con destino
NARNIA y otra sin nombre de pasajero

## Modalidades

Modalidad total procesa todas las lineas del CSV de una vez y genera todos los
ficheros de destino

Modalidad linea a linea procesa la linea indicada del CSV, la anade a su
fichero de destino y reconstruye ese fichero con las lineas anteriores que
pertenecen al mismo pais y fecha. La linea se indica con su numero fisico en el
fichero, la 2 es la primera reserva porque la 1 es la cabecera

## Interfaz web

Panel de entrada con selector de fichero del servidor y subida de un CSV propio

Selector de modalidad, total o linea a linea con su numero de linea

Resumen con lineas leidas, reservas validas, reservas con localizador,
ficheros generados, paises destino y lineas descartadas

Resumen por pais de destino con enlace a cada fichero

Tabla de ficheros con ver y descargar

Log del proceso agrupado por destino

Detalle linea a linea con identificador, destino, fichero asignado y localizador
cuando hay coincidencia

Vista previa del contenido de cada fichero generado

## Migraciones

El proyecto se puede migrar a otra tecnologia del enunciado. Puntos de
contacto recomendados

| Modulo              | Que habria que cambiar                        |
| ------------------- | --------------------------------------------- |
| airtortilla/paises.py  | Catalogo, se puede sustituir por una API externa |
| airtortilla/lector_csv.py | Lectura, se puede cambiar por una libreria de CSV |
| airtortilla/modelos.py  | Entidad y calculo de identificador y localizador |
| airtortilla/procesador.py | Nucleo del agrupado por pais de destino      |
| airtortilla/vistas.py   | Interfaz, se puede migrar a React Vue o similar |
| airtortilla/servidor.py | Servidor, se puede migrar a FastAPI o Django   |
