"""Catalogos y jerarquias conceptuales de ObraPrecio.

Jerarquia geografica:  ciudad -> estado -> region -> pais
Jerarquia temporal:    mes -> trimestre -> anio
Jerarquia de inflacion: variacion anual (%) -> nivel (deflacion ... muy alta)

Las regiones siguen la regionalizacion que usa Banco de Mexico en su Reporte sobre
las Economias Regionales (Norte, Centro Norte, Centro, Sur).

La fuente escribe las ciudades con abreviaturas irregulares ("Villahermosa,Tab.",
"Cd. Jimenez Chih."). Aqui se fija el nombre limpio de cada una; una ciudad que no
este en el catalogo no se adivina: sus registros se van a cuarentena.
"""

import unicodedata

REGIONES = {
    "Norte": ["Baja California", "Chihuahua", "Coahuila", "Nuevo León", "Sonora", "Tamaulipas"],
    "Centro Norte": [
        "Aguascalientes",
        "Baja California Sur",
        "Colima",
        "Durango",
        "Jalisco",
        "Michoacán",
        "Nayarit",
        "San Luis Potosí",
        "Sinaloa",
        "Zacatecas",
    ],
    "Centro": [
        "Ciudad de México",
        "Estado de México",
        "Guanajuato",
        "Hidalgo",
        "Morelos",
        "Puebla",
        "Querétaro",
        "Tlaxcala",
    ],
    "Sur": [
        "Campeche",
        "Chiapas",
        "Guerrero",
        "Oaxaca",
        "Quintana Roo",
        "Tabasco",
        "Veracruz",
        "Yucatán",
    ],
}
REGION_DE_ESTADO = {e: r for r, estados in REGIONES.items() for e in estados}

# nombre en la fuente -> (ciudad limpia, estado)
CIUDADES = {
    "Nacional": ("Nacional", "Nacional"),
    "Área Metropolitana de la Cd. de México": ("Ciudad de México (AM)", "Ciudad de México"),
    "Mérida, Yuc.": ("Mérida", "Yucatán"),
    "Morelia, Mich.": ("Morelia", "Michoacán"),
    "Guadalajara, Jal.": ("Guadalajara", "Jalisco"),
    "Monterrey, N.L.": ("Monterrey", "Nuevo León"),
    "Mexicali, B. C.": ("Mexicali", "Baja California"),
    "Juárez, Chih.": ("Ciudad Juárez", "Chihuahua"),
    "Acapulco, Gro.": ("Acapulco", "Guerrero"),
    "Culiacán, Sin.": ("Culiacán", "Sinaloa"),
    "León, Gto.": ("León", "Guanajuato"),
    "Puebla, Pue.": ("Puebla", "Puebla"),
    "San Luis Potosí, S.L.P.": ("San Luis Potosí", "San Luis Potosí"),
    "Tapachula, Chis.": ("Tapachula", "Chiapas"),
    "Toluca, Edo. de Méx.": ("Toluca", "Estado de México"),
    "Torreón, Coah.": ("Torreón", "Coahuila"),
    "Veracruz, Ver.": ("Veracruz", "Veracruz"),
    "Villahermosa,Tab.": ("Villahermosa", "Tabasco"),
    "Tampico, Tamps.": ("Tampico", "Tamaulipas"),
    "Chihuahua, Chih.": ("Chihuahua", "Chihuahua"),
    "Hermosillo, Son.": ("Hermosillo", "Sonora"),
    "Monclova, Coah.": ("Monclova", "Coahuila"),
    "Córdoba, Ver.": ("Córdoba", "Veracruz"),
    "Aguascalientes, Ags.": ("Aguascalientes", "Aguascalientes"),
    "Tijuana, B. C.": ("Tijuana", "Baja California"),
    "Matamoros, Tamps.": ("Matamoros", "Tamaulipas"),
    "Colima, Col.": ("Colima", "Colima"),
    "La Paz, B. C. S.": ("La Paz", "Baja California Sur"),
    "Chetumal, Q. R.": ("Chetumal", "Quintana Roo"),
    "Jacona, Mich.": ("Jacona", "Michoacán"),
    "Fresnillo, Zac.": ("Fresnillo", "Zacatecas"),
    "Iguala, Gro.": ("Iguala", "Guerrero"),
    "Huatabampo, Son.": ("Huatabampo", "Sonora"),
    "Tulancingo, Hgo.": ("Tulancingo", "Hidalgo"),
    "Cortazar, Gto.": ("Cortazar", "Guanajuato"),
    "Cd. Jiménez Chih.": ("Ciudad Jiménez", "Chihuahua"),
    "Durango, Dgo.": ("Durango", "Durango"),
    "Tepic, Nay.": ("Tepic", "Nayarit"),
    "Oaxaca, Oax.": ("Oaxaca", "Oaxaca"),
    "Querétaro, Qro.": ("Querétaro", "Querétaro"),
    "Cuernavaca, Mor.": ("Cuernavaca", "Morelos"),
    "Tlaxcala, Tlax.": ("Tlaxcala", "Tlaxcala"),
    "San Andrés Tuxtla, Ver.": ("San Andrés Tuxtla", "Veracruz"),
    "Campeche, Camp.": ("Campeche", "Campeche"),
    "Tepatitlán, Jal.": ("Tepatitlán", "Jalisco"),
    "Tehuantepec, Oax.": ("Tehuantepec", "Oaxaca"),
    "Cd. Acuña, Coah.": ("Ciudad Acuña", "Coahuila"),
}

COMPONENTES = ("general", "materiales", "maquinaria", "mano_obra")

MESES = {
    "Ene": 1,
    "Feb": 2,
    "Mar": 3,
    "Abr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dic": 12,
}

# Discretizacion de la variacion anual del indice (puntos de corte en %).
# El 3 % es la meta de inflacion de Banco de Mexico y 4 % el techo de su intervalo.
CORTES_INFLACION = [float("-inf"), 0.0, 3.0, 6.0, 10.0, float("inf")]
NIVELES_INFLACION = ["deflacion", "baja", "moderada", "alta", "muy_alta"]


def slug(texto):
    """'San Luis Potosí' -> 'san_luis_potosi' (clave estable, sin acentos)."""
    plano = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "_".join("".join(c if c.isalnum() else " " for c in plano.lower()).split())


def ciudad(nombre_fuente):
    """Devuelve dict con la jerarquia geografica o None si la ciudad no esta catalogada."""
    par = CIUDADES.get((nombre_fuente or "").strip())
    if par is None:
        return None
    nombre, estado = par
    return {
        "ciudad": nombre,
        "ciudad_id": slug(nombre),
        "estado": estado,
        "region": REGION_DE_ESTADO.get(estado, "Nacional"),
    }
