CABECERA = "fecha_reserva;origen;destino;nombre_pasajero;localizador"

LINEAS = [
    ["2026-10-02", "ESPANA", "FRANCIA", "LUCIA MORENO", ""],
    ["2026-10-02", "ESPANA", "FRANCIA", "MARCOS RUIZ", ""],
    ["2026-10-02", "ITALIA", "FRANCIA", "MARCOS RUIZ", ""],
    ["2026-10-02", "ALEMANIA", "JAPON", "ANNA SCHMIDT", ""],
    ["2026-10-02", "ALEMANIA", "JAPON", "ANNA SCHMIDT", ""],
    ["2026-10-02", "ALEMANIA", "JAPON", "ANNA SCHMIDT", ""],
    ["2026-10-02", "ALEMANIA", "JAPON", "ANNA SCHMIDT", ""],
    ["2026-10-02", "FRANCIA", "JAPON", "ANNA SCHMIDT", ""],
    ["2026-10-02", "ALEMANIA", "JAPON", "ANNA SCHMIDT", ""],
    ["2026-10-02", "PORTUGAL", "BRASIL", "JOAO SILVA", ""],
    ["2026-10-02", "PORTUGAL", "BRASIL", "JOAO SILVA", ""],
    ["2026-10-03", "ESPANA", "ESTADOS UNIDOS", "MARIA LOPEZ", ""],
    ["2026-10-03", "ESPANA", "ESTADOS UNIDOS", "CARLOS GOMEZ", ""],
    ["2026-10-03", "REINO UNIDO", "ESTADOS UNIDOS", "PETER BROWN", ""],
    ["2026-10-03", "ESPANA", "JAPON", "MARTA GARCIA", ""],
    ["2026-10-03", "MEXICO", "ESPANA", "DIEGO FERNANDEZ", ""],
    ["2026-10-03", "MEXICO", "ESPANA", "DIEGO FERNANDEZ", ""],
    ["2026-10-04", "ALEMANIA", "ITALIA", "HANNA WEBER", ""],
    ["2026-10-04", "FRANCIA", "ESPANA", "JULIE MARTIN", ""],
    ["2026-10-04", "FRANCIA", "ESPANA", "PIERRE DUPONT", ""],
    ["2026-10-04", "CHINA", "ESPANA", "LI WEI", ""],
    ["2026-10-05", "NORUEGA", "ISLANDIA", "OLAV NILSEN", ""],
    ["2026-10-05", "NORUEGA", "ISLANDIA", "OLAV NILSEN", ""],
    ["2026-10-05", "SUECIA", "ISLANDIA", "EVA LIND", ""],
    ["2026-10-05", "ARGENTINA", "URUGUAY", "LUCIA PAZ", ""],
    ["2026-10-06", "INDIA", "EMIRATOS ARABES UNIDOS", "RAJ PATEL", ""],
    ["2026-10-06", "INDIA", "EMIRATOS ARABES UNIDOS", "RAJ PATEL", ""],
    ["2026-10-06", "AUSTRALIA", "NUEVA ZELANDA", "JACK MURPHY", ""],
    ["2026-10-07", "BELGICA", "PAISES BAJOS", "JAN PEETERS", ""],
    ["2026-10-07", "SUIZA", "PAISES BAJOS", "CLAUDE WEBER", ""],
    ["2026-10-07", "PERU", "CHILE", "ANA TORRES", ""],
    ["2026-10-07", "PERU", "CHILE", "ANA TORRES", ""],
    ["2026-10-08", "TURQUIA", "GRECIA", "MEHMET YILMAZ", ""],
    ["2026-10-08", "CANADA", "MARRUECOS", "SARAH TREMBLAY", ""],
    ["2026-10-08", "RUSIA", "FINLANDIA", "IVAN VOLKOV", ""],
    ["2026-10-09", "ESPANA", "CUBA", "ANA MORALES", ""],
    ["2026-10-09", "REP DOMINICANA", "CUBA", "PEDRO RAMIREZ", ""],
    ["2026-10-09", "VENEZUELA", "COLOMBIA", "ANA MORALES", ""],
    ["2026-10-09", "ECUADOR", "COLOMBIA", "DIEGO PAZ", ""],
    ["2026-10-10", "IRLANDA", "REINO UNIDO", "SEAN KELLY", ""],
    ["2026-10-10", "IRLANDA", "REINO UNIDO", "SEAN KELLY", ""],
    ["2026-10-10", "ISLAS BAHAMAS", "PANAMA", "JOHN SMITH", ""],
    ["2026-10-10", "SENEGAL", "MARRUECOS", "AMADOU DIALLO", ""],
    ["2026-10-11", "UCRANIA", "POLONIA", "OLEKSANDR PETRENKO", ""],
    ["2026-10-11", "RUMANIA", "HUNGRIA", "ION POPESCU", ""],
    ["2026-10-11", "GRECIA", "CHIPRE", "YANNIS NIKOLOU", ""],
    ["2026-10-11", "KAZAJSTAN", "UZBEKISTAN", "ALEXEY VOLKOV", ""],
    ["2026-10-12", "THAILANDIA", "JAPON", "SOMCHAI PONG", ""],
    ["2026-10-12", "AUSTRALIA", "JAPON", "EMILY CLARKE", ""],
    ["2026-10-12", "COLOMBIA", "PERU", "CARLOS RAMOS", ""],
]

LINEAS_FUERA_CATALOGO = [
    ["2026-10-13", "ESPANA", "NARNIA", "PABLO GARRIDO", ""],
    ["2026-10-13", "ESPANA", "ESPANA", "", ""],
]


def obtener_lineas_csv(incluir_errores=True):
    filas = [CABECERA]
    for linea in LINEAS:
        filas.append(";".join(linea))
    if incluir_errores:
        for linea in LINEAS_FUERA_CATALOGO:
            filas.append(";".join(linea))
    return "\n".join(filas) + "\n"


def obtener_lineas():
    return [linea[:] for linea in LINEAS]
