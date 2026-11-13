# Cambio de tema: de Observatorio Eléctrico a ObraPrecio

Actualiza la [propuesta de E0](../E0/propuesta.md). La etiqueta `e0` no se modifica; este documento registra qué cambió y por qué.

## 1. Por qué se cambió
La propuesta de E0 medía el precio horario de la electricidad en Colima. Los datos y la captura funcionan, pero al buscar quién pagaría por el producto no se encontró un cliente al alcance del equipo. El proyecto exige un cliente real y un modelo de negocio, así que se evaluaron alternativas con cuatro reglas: datos públicos, problema real, cero datos personales y factible en un semestre.

| Idea | Motivo de descarte |
|---|---|
| Precio de la electricidad (E0) | Datos públicos y captura lista, pero sin cliente que pague al alcance del equipo |
| Plátano y agricultura | Otro equipo ya lo trabaja; demasiado amplio para un semestre |
| Sistema médico | Los datos de pacientes no pueden estar en un repositorio público |
| Remesas | Muy pocas variables para cubrir las tres materias |

## 2. Qué es ObraPrecio
**Pregunta:** ¿cuánto ha subido el costo de construir una vivienda en mi ciudad y qué lo está moviendo: los materiales, la maquinaria o la mano de obra?

**Usuarios:** quien va a construir o ampliar su casa, albañiles y contratistas que cotizan, arquitectos y ferreterías.

**Hipótesis de negocio (por validar en entrevistas):** suscripción para contratistas y arquitectos, espacio pagado para ferreterías, reportes por ciudad y un nivel gratuito limitado. Ninguna cifra de precio está validada todavía.

## 3. Fuentes
| Fuente | Qué aporta | Acceso | Frecuencia |
|---|---|---|---|
| INEGI, Índice Nacional de Precios Productor, "Construcción residencial por ciudad" (base julio 2019 = 100) | Índice general y tres componentes (materiales, alquiler de maquinaria, mano de obra) para 46 ciudades y el total nacional; mensual; Nacional desde 1973, 23 ciudades desde 1981 y 23 desde diciembre de 2003 (Colima entre ellas) | Consulta pública del sitio de índices de precios, sin llave; exportación CSV | Semanal (lunes) en GitHub Actions; el índice es mensual |
| Banxico, API del SIE, serie SF43718 | Tipo de cambio FIX | API con token gratuito (secret `BANXICO_TOKEN`) | Diaria (ya activa desde E0) |

**Revisión ética y legal de INEGI.** `https://www.inegi.org.mx/robots.txt` permite `/app` (consultado el 13 de noviembre de 2026). El extractor se identifica con el User-Agent del proyecto y el correo de contacto, espera al menos 1.5 s entre peticiones y hace 4 peticiones por captura. La información es estadística pública agregada: no contiene datos personales. Los términos de libre uso de la información de INEGI piden citar la fuente; se cita en el README y en cada tabla.

## 4. Preguntas analíticas
1. **Pronóstico (E1, Estadística):** índice general y por componente de una ciudad, con suavizamiento simple, Holt, Holt-Winters y ARIMA/SARIMA.
2. **Comparación entre ciudades y regiones:** ¿hay diferencias sistemáticas en la inflación de la construcción entre regiones?
3. **Relación con el tipo de cambio:** ¿el FIX anticipa el costo de los materiales?

## 5. Qué se conserva de E0
La arquitectura medallón, el extractor ético, la bitácora de captura, las pruebas y el flujo de GitHub Actions se reutilizan sin cambios. La captura de CENACE sigue activa; se decidirá en E2 si se apaga. Los objetivos de calidad se mantienen: disponibilidad de la captura ≥ 95 %, MTTR ≤ 24 h y completitud ≥ 99 % (ahora medida sobre las 188 series del índice).

## 6. Pendientes
- Entrevistas con albañil, contratista, arquitecto, ferretería y una persona que haya construido su casa.
- Confirmar con los tres docentes el cambio de tema y la participación de José Rey solo en Calidad.
- Localizar la estructura vigente del índice (los datos de la estructura consultada terminan en julio de 2025).
