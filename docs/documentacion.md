# Documentacion tecnica

Complemento del README con el detalle de diseno, las decisiones tomadas y el
momento de cada una, para dejar constancia de las migraciones y cambios
segun pide el enunciado.

## 0 Integrantes y reparto

| Integrante | Reparto |
| ---------- | ------- |
| Marco | Interfaz web en HTML, log del proceso, vista previa y descarga de los ficheros, identificador unico y localizador de coincidencias, documentacion |
| Sebas | Lectura del CSV de entrada, catalogo de paises e IATA, agrupacion por pais de destino y generacion de los ficheros AirTortilla_XX_YYYY_MM_DD, CSV de ejemplo y pruebas automaticas |

### 0.1 Detalle de la parte de Sebas

| Elemento del reparto | Donde esta implementado | Pruebas |
| -------------------- | ----------------------- | ------- |
| Lectura del CSV de entrada | airtortilla/lector_csv.py, leer_texto y leer_reservas | PruebaLecturaCsv |
| Catalogo de paises e IATA | airtortilla/paises.py, CODIGO_IATA_POR_PAIS y codigo_iata | PruebaCatalogoPaises, PruebaPaises |
| Agrupacion por pais de destino | airtortilla/procesador.py, clave_agrupacion_destino | PruebaAgrupacionPorPais, PruebaProcesoTotal |
| Generacion de los ficheros AirTortilla_XX_YYYY_MM_DD | airtortilla/procesador.py, nombre_fichero y procesar_reservas | PruebaNombreFichero, PruebaAgrupacionPorPais |
| CSV de ejemplo | data/reservas_entrada.csv y airtortilla/datos_ejemplo.py | PruebaCsvEjemplo |
| Pruebas automaticas | tests/test_lectura_csv.py y tests/test_airtortilla.py | 54 pruebas |

La lectura del CSV no depende de la codificacion del fichero. leer_texto abre el
fichero en binario, quita el BOM si lo hay y prueba utf-8, cp1252 y latin-1 en
ese orden, de forma que un CSV guardado desde Windows con acentos se lee igual
que uno guardado en UTF-8

El catalogo de paises esta en un solo diccionario para que se pueda ampliar sin
tocar el resto. Admite el nombre del pais, el nombre con o sin tildes, el
codigo IATA de dos letras directamente y una lista de sinonimos como EEUU o
HOLANDA. La clave de agrupacion es el codigo IATA del destino mas la fecha, que
es lo que define el nombre del fichero de salida

Decision registrada en la version 1.2.0 del 7 de octubre de 2026

## 1 Requisitos que cubre la solucion

| Requisito | Donde se resuelve |
| --------- | ---------------- |
| Leer un CSV con Destino, Origen y Nombre del Pasajero | airtortilla/lector_csv.py |
| Identificacion inequivoca de cada reserva | airtortilla/modelos.py, campo id_reserva |
| Localizador cuando coinciden nombre, origen y destino | airtortilla/modelos.py, resolver_localizadores |
| Minimo 3 casos de coincidencia, uno de 5 personas | data/reservas_entrada.csv |
| Ficheros AirTortilla_XX_YYYY_MM_DD por pais de destino | airtortilla/procesador.py, nombre_fichero |
| Interfaz que activa las funciones | airtortilla/servidor.py y airtortilla/vistas.py |
| Modalidad total y modalidad linea a linea | airtortilla/procesador.py, parametro solo_linea |
| Ver el proceso de golpe | airtortilla/procesador.py, claves log y detalle |

## 2 Decisiones de diseno

### 2.1 Un fichero por pais de destino y fecha

El enunciado fija el nombre AirTortilla_XX_YYYY_MM_DD, que incluye la fecha de
la reserva. Por eso la clave de agrupacion es la pareja codigo IATA de destino
mas fecha, y no solo el pais

Decision registrada en la version 1.0.0 del 5 de octubre de 2026

### 2.2 Catalogo de paises propio

Se incluye un catalogo de pais con su codigo IATA en airtortilla/paises.py para
no depender de internet ni de una libreria externa

La normalizacion quita tildes y pasa a mayusculas, de forma que el CSV puede
llegar con o sin tildes y tambien con el codigo IATA escrito directamente. Si
mas adelante se quiere una fuente externa basta con cambiar ese modulo

### 2.3 Delimitador y cabeceras automaticos

El lector detecta el separador mas frecuente entre punto y coma, coma,
tabulador y barra vertical. Las cabeceras se comparan tras normalizar, asi que
Destino, destino, DESTINO o destino_pais funcionan igual

Decision registrada en la version 1.0.0 del 5 de octubre de 2026

### 2.4 Identificador derivado del contenido

id_reserva se calcula con SHA-1 sobre fecha, origen, destino y nombre mas un
contador de repeticiones de esa misma combinacion

Se eligio esta forma en lugar de un contador correlativo porque el resultado es
estable entre ejecuciones. Si el mismo CSV se procesa dos veces se obtienen los
mismos identificadores, lo que permite comparar ficheros y hacerMerge sin
temor a que cambien los ids

Decision registrada en la version 1.0.0 del 5 de octubre de 2026

### 2.5 Localizador derivado del grupo

El localizador se calcula sobre nombre, origen y destino normalizados del grupo
coincidente. Formato LOC- mas seis caracteres del nombre mas guion mas cuatro
caracteres del grupo

No se usa un contador porque el localizador debe describir al grupo y no al
orden de lectura. Ademas el campo localizador del CSV de entrada tiene
prioridad, de forma que si la reserva ya trae localizador de un sistema previo
se conserva

Decision registrada en la version 1.0.0 del 5 de octubre de 2026

### 2.6 Las lineas invalidas no generan fichero

Una reserva con un campo obligatorio vacio, una fecha no reconocida o un destino
fuera del catalogo se descarta y se informa del motivo en el log

Antes se generaba un fichero AirTortilla_ERROR_ para agrupar los errores, pero
incumplia el formato exigido y mezclaba datos invalidos con validos. Se cambio
para que todos los ficheros generados respeten AirTortilla_XX_YYYY_MM_DD

Cambio registrado en la version 1.0.1 del 5 de octubre de 2026

### 2.7 Numero de linea fisico

En modalidad linea a linea el numero pedido es la linea fisica del CSV, la 2
es la primera reserva porque la 1 es la cabecera

Se uso el numero de registro de datos en lugar del numero de linea fisico y se
cambio para que el numero que ve el usuario en un editor de texto coincida con
el que introduce en la interfaz

Cambio registrado en la version 1.0.1 del 5 de octubre de 2026

### 2.8 Modalidad linea a linea reconstruye el fichero

Al procesar una sola linea se rehace su fichero de destino con las lineas
anteriores que pertenecen al mismo pais y fecha. Asi el resultado es el mismo
que en modalidad total para ese fichero y no se pierde informacion

Ademas los localizadores se calculan sobre el conjunto de lineas ya procesadas
mas la linea actual, de forma que un pasajero que coincide con uno anterior ya
recibe localizador en la primera aparicion

Cambio registrado en la version 1.0.1 del 5 de octubre de 2026

## 3 Arquitectura

Hay dos implementaciones del mismo nucleo

```
index.html  CATALOGO, construirReservas, resolverLocalizadores, procesar, crearZip
```

```
datos_ejemplo.py  genera el CSV de ejemplo
        |
        v
lector_csv.py  texto -> lista de Reserva
        |
        v
modelos.py  validacion, id_reserva y localizadores
        |
        v
procesador.py  agrupado por IATA y fecha -> ficheros de salida
        |
        v
vistas.py  HTML de la interfaz
        |
        v
servidor.py  rutas HTTP, subida de ficheros y descarga
```

index.html es la entrega principal, se abre con doble clic y no necesita servidor
ni instalar nada

La version en Python hace lo mismo pero escribe los ficheros en el disco dentro
de data/salida y ademas trae 54 pruebas automaticas

Ambas implementaciones se han comprobado linea a linea y generan exactamente
los mismos ficheros, los mismos identificadores y los mismos localizadores. Por
ejemplo para la linea 7 del CSV de ejemplo las dos devuelven
RES-6YY590FJZK y LOC-ANNASC-AM18

### 3.1 Por que la entrega principal es un HTML suelto

Un navegador abre fichero con doble clic y ya funciona, sin terminal, sin
servidor y sin instalar dependencias, que es lo que se pide en una presentacion

El limite es que por seguridad el navegador no puede escribir dentro de una
carpeta del disco. Los ficheros se generan en memoria y se descargan. Para
tenerlos ya escritos en una carpeta del disco esta la version en Python

Por eso el boton de descarga genera un unico ZIP con los 28 CSV dentro de una
carpeta salida. El ZIP se construye a mano con cabeceras locales, directorio
central y registro final, con CRC-32 y sin compresion

### 3.2 SHA-1 en JavaScript

El identificador de reserva usa SHA-1 para que sea el mismo en las dos
implementaciones. En index.html se implementa a mano porque crypto.subtle solo
esta disponible en contexto seguro y no funciona siempre al abrir un fichero
con doble clic

La implementacion se valido contra los vectores de prueba conocidos, sha1 de la
cadena vacia y sha1 de abc, y contra los valores que produce Python

cli.py es la entrada de terminal y llama a las mismas funciones que la interfaz
web, de forma que las dos modalidades se comportan igual

## 4 Formato de los ficheros

Entrada, separador automatico

```
fecha_reserva;origen;destino;nombre_pasajero;localizador
2026-10-02;ESPANA;FRANCIA;LUCIA MORENO;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
```

Salida

```
id_reserva;fecha_reserva;destino;destino_iata;origen;nombre_pasajero;localizador;coincidencia;viajero_en_grupo
RES-5B98EBNRRC;2026-10-02;FRANCIA;FR;ESPANA;LUCIA MORENO;;NO;1
RES-1CGMF3RFYM;2026-10-02;JAPON;JP;ALEMANIA;ANNA SCHMIDT;LOC-ANNASC-AM18;SI;5
```

## 5 Casos de coincidencia del fichero de ejemplo

Caso 1, dos pasajeros con el mismo nombre y destino pero distinto origen

```
2026-10-02;ESPANA;FRANCIA;MARCOS RUIZ;
2026-10-02;ITALIA;FRANCIA;MARCOS RUIZ;
```

Comparten nombre y destino pero el origen es distinto, por eso cada uno tiene
su propio id_reserva y ninguno lleva localizador

Caso 2, cinco pasajeros identicos

```
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
2026-10-02;ALEMANIA;JAPON;ANNA SCHMIDT;
```

Los cinco comparten nombre, origen y destino, por eso los cinco reciben el
mismo localizador LOC-ANNASC-AM18 y el campo viajero_en_grupo vale 5

Adyacente a este caso hay una septima linea con el mismo nombre y destino pero
origen FRANCIA, que queda fuera del grupo

Caso 3, dos pasajeros identicos en otro destino

```
2026-10-02;PORTUGAL;BRASIL;JOAO SILVA;
2026-10-02;PORTUGAL;BRASIL;JOAO SILVA;
```

Comparten localizador LOC-JOAOSI-K1YR

## 6 Resultado del proceso de ejemplo

```
Leidas 52 | Validas 50 | Con localizador 17 | Descartadas 2
```

Se generan 28 ficheros repartidos en 24 paises de destino distintos, entre los
que estan Francia, Japon, Espana, Estados Unidos, Brasil, Italia, Canada y
Marruecos

## 7 Pruebas

```
python -m unittest discover -s tests
```

54 pruebas repartidas en dos ficheros, test_airtortilla.py y test_lectura_csv.py

| Grupo            | Cobertura                                        |
| ---------------- | ------------------------------------------------ |
| PruebaPaises     | Codigo IATA con y sin tildes, codigo directo, pais desconocido |
| PruebaCatalogoPaises | Sinonimos, codigos de dos letras, destinos del CSV de ejemplo catalogados |
| PruebaFechas     | Formatos aceptados y fecha invalida              |
| PruebaNombreFichero | Formato AirTortilla_XX_YYYY_MM_DD             |
| PruebaProcesoTotal | Un fichero por pais, formato de nombre, ids unicos, grupo de 5, tres casos de coincidencia, lineas invalidas descartadas |
| PruebaProcesoLinea | Una sola linea, cabecera, linea inexistente    |
| PruebaReinicio   | Borrado solo de ficheros AirTortilla             |
| PruebaInterfazWeb | Inicio, modalidad total, modalidad linea a linea, subida de fichero sin pisar el original |
| PruebaLecturaCsv | UTF-8 con BOM, cp1252, latin-1, texto pegado, delimitador, cabeceras, numeros de linea |
| PruebaAgrupacionPorPais | Un fichero por pais y fecha, nombre del fichero, lineas invalidas sin fichero |
| PruebaCsvEjemplo | Existe, 52 reservas, tres casos de coincidencia, grupo de 5, dos lineas invalidas, 28 ficheros |

## 8 Rutas de la interfaz web

| Ruta                     | Metodo | Descripcion                                |
| ------------------------ | ------ | ------------------------------------------ |
| /                        | GET    | Panel principal                            |
| /procesar                | POST   | Ejecuta el proceso y vuelve al panel       |
| /limpiar                 | POST   | Borra los ficheros generados               |
| /fichero/nombre.csv      | GET    | Muestra el contenido de un fichero         |
| /descargar/nombre.csv    | GET    | Descarga el fichero                        |
| /salida                  | GET    | Listado plano de los ficheros generados    |

## 9 Puntos de migracion

Si se pide migrar a otra tecnologia del enunciado

| Destino    | Cambios necesarios                                                     |
| ---------- | ---------------------------------------------------------------------- |
| Java       | Reescribir los modulos como clases, usar java.nio y una libreria CSV     |
| C#         | Reescribir los modulos, usar System.IO y una libreria CSV              |
| Go         | Reescribir los modulos, usar encoding/csv                              |
| Node.js    | Portar lector, modelos y procesador, Express en lugar del servidor http |
| PHP        | Portar los modulos a funciones o clases, PHP built in server            |

El nucleo a migrar es siempre el mismo, la funcion procesar_reservas de
airtortilla/procesador.py, que agrupa por codigo IATA y fecha y escribe un
fichero por grupo

## 10 Registro de versiones

| Version   | Fecha      | Cambios                                                                 |
| --------- | ---------- | ----------------------------------------------------------------------- |
| 1.0.0     | 2026-10-05 | Primera entrega, lectura de CSV, identificador, localizador, agrupado por pais de destino, interfaz web con las dos modalidades |
| 1.0.1     | 2026-10-05 | Las lineas invalidas ya no generan ficheros, el numero de linea pasa a ser el fisico del CSV, la modalidad linea a linea reconstruye el fichero de destino y calcula los localizadores sobre lo ya procesado, subida de ficheros corregida para no pisar el CSV del servidor |
| 1.0.2     | 2026-10-05 | Se anade al README y a esta documentacion el reparto de trabajo entre Marco y Sebas |
| 1.1.0     | 2026-10-05 | index.html pasa a ser la entrega principal, interfaz web completa en un solo fichero sin servidor ni dependencias. Se corrige el catalogo de paises para los nombres con espacio y se reescribe el SHA-1 en JavaScript para que genere los mismos identificadores y localizadores que la version en Python. Se anade la descarga de todos los ficheros en un ZIP construido a mano |
| 1.2.0     | 2026-10-07 | Se documenta la parte de Sebas en el apartado 0.1. Se anaden las pruebas automaticas de esa parte en tests/test_lectura_csv.py, que cubren la lectura del CSV en utf-8, cp1252 y latin-1, el catalogo de paises, la agrupacion por pais y fecha y el CSV de ejemplo. La suite pasa de 23 a 54 pruebas |
