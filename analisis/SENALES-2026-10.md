# Libro de señales de demanda — Gucci (sell-in real, regulares)

**Qué es:** combinaciones de indicadores, visibles el día de la foto, que anticipan **lo que de verdad va a pasar con el sell-in** de un código y qué hacer al verlas.
No se usa el Consensus en ningún sitio. Ni como indicador ni como referencia.

**Cómo se encontraron:**
- Se dejó que el ordenador buscara solo entre 75 indicadores y sus combinaciones (~200.000 reglas por evento).
- Solo quedan las que se cumplen en **las 4 particiones** de los datos: periodo antiguo (2023.M06-2025.M02), periodo reciente (2025.M03-2026.M08) y cada mitad de los códigos.
- Además tienen que repetirse en al menos 4 meses distintos.

**Datos:** 3.370 casos código × mes, 128 regulares con ≥ 150 uds/año y más de 12 meses de vida. El perímetro está armonizado (ver anexo).

"Esperable" = nivel del código en los últimos 12 meses × estacionalidad de su brand el año pasado. "Mediana" = lo que vendió el código típico en ese caso.

---

## 1. Las señales se suman

| Evento | Sin señales | 1 señal | **2 o más señales** | Mediana con 2+ |
|---|---|---|---|---|
| **Caída** de un código hoy sano (< 0,5 × lo esperable en 3M) | 19 % | 45 % | **69 %** [58-78] (antiguo 64 % · reciente 79 %) | 0,26 × lo esperable |
| **Muerte** de un código hoy sano (< 20 % de su ritmo en 6M) | 4 % | 15 % | **45 %** [36-55] (47 % · 43 %) | 0,24 × su ritmo |
| **Pedido grande** el mes que viene | 8 % | 27 % | **42 %** [28-58] | 1,55 × su media |
| **Subida fuerte** (> 1,5 × lo esperable en 3M) | 10 % | 28 % | **40 %** [30-51] | 1,22 × lo esperable |
| **Mes vacío** el mes que viene (< 25 % de la media) | 20 % | 77 % | **81 %** [77-84] | 0 |

Las señales de cada evento están abajo. "Sano" = últimos 3 meses ≥ 60 % de su ritmo y sin meses a cero.

---

## 2. Señales y acciones

### A. CAÍDA — ¿este código, que hoy va bien, se va a hundir? (base 24 %)

| # | Si ves… | Se cumple | Antiguo · reciente · mitad A · mitad B |
|---|---|---|---|
| C1 | **Código errático** (CV mensual ≥ 0,9) **y pequeño** (< 4.000 uds/año) **cuyo último mes fue < 30 % de su media** | **69 %** [54-81] · 24 cód. | 64 · 79 · 70 · 67 |
| C5 | Muy errático (CV ≥ 1,25) y pequeño | **60 %** [50-69] · 32 cód. | 56 · 70 · 62 · 57 |
| C3 | **Crece ≥ 6 veces más que su PL mientras la PL cae ≥ 40 %** (el que va contra su línea acaba cayendo) | **58 %** [47-68] · 39 cód. | 62 · 48 · 73 · 48 |
| C4 | **La brand está en campaña de One Shots** (los One Shots venden ≥ 70 % de lo que venden los regulares en 3M) **y el código es de ≥ 150 ml** | **57 %** [46-67] · 16 cód. | 62 · 55 · 100 · 42 |
| C2 | Crece ≥ 4 veces más que su brand y es errático | 54 % [45-64] | 61 · 37 · 52 · 57 (más débil en el periodo reciente) |

**Acción:**
- Con 2+ señales, bajar el forecast de los próximos 3 meses a **~0,3-0,4 × lo esperable**. Con 1 señal, a ~0,6 ×.
- No extrapolar un buen trimestre de un código errático o que va contra su línea.
- C4 es canibalismo: durante una campaña fuerte de One Shots, los tamaños grandes regulares (≥ 150 ml) pierden. Los de 50-100 ml no (24 %, igual que la base).

### B. MUERTE — ¿este código va a dejar de venderse en 6 meses? (base 8 %)

| # | Si ves… | Se cumple | Antiguo · reciente · A · B |
|---|---|---|---|
| M1 | **Pequeño (< 4.000 uds/año), errático (CV ≥ 1) y su PL cae ≥ 30 %** | **49 %** [36-63] · 24 cód. | 57 · 37 · 61 · 38 |
| M2 | **Rabbit cuyo EPOS va ≥ 25 % peor que el EPOS de su brand** | **36 %** [24-49] · 21 cód. | — · 36 · 42 · 28 (solo periodo con EPOS) |
| M3 | **Pico aislado:** muy errático (CV ≥ 1,25) y con un pedido grande en los últimos 3 meses | 30 % [22-39] · 31 cód. | 27 · 37 · 33 · 26 |
| M5 | Pequeño y su PL cae ≥ 30 % | 30 % [23-38] · 38 cód. | 29 · 32 · 36 · 23 |
| M4 | Tamaño ≥ 150 ml con un pedido grande en los últimos 2 meses | 27 % [18-38] · 18 cód. | 25 · 30 · 45 · 20 |

**Acción:**
- Con 2+ señales (45 % de muerte frente al 4 % sin señales), **no reponer**: no fabricar contra el forecast, poner ese código en la lista de phase-out y pasar el volumen al hermano sano de la línea.
- Un pedido grande en un código errático **no anuncia una recuperación**: suele ser el último.

### C. PEDIDO GRANDE el mes que viene (≥ 2 × la mediana de 12M; base 11 %)

| # | Si ves… | Se cumple | Mediana |
|---|---|---|---|
| G1 | **Re-pedido tras corte:** código irregular (≥ 2 meses a cero en 12M), con pedido grande en los últimos 2 meses **y cortes ≥ 0,5 meses de venta** | **38 %** [27-51] · 21 cód. | 1,30 × su media |
| G3 | La brand cae ≥ 25 % en sell-in **pero sus One Shots crecen ≥ 2,5 veces**, y el código pide todos los meses | 31 % [23-40] · 79 cód. | 1,08 × |
| G2 | **Estantería vacía:** cortes ≥ 2 meses de venta y EPOS de los últimos 3M ≤ 0,65 × su media | 29 % [21-40] · 29 cód. | 0,80 × |
| G4 | **Septiembre** y el código pide todos los meses | 27 % [21-33] · 107 cód. | 1,11 × |

**Acción:** con 2+ señales (42 % frente al 8 %), **asegurar supply y stock para el mes siguiente** por ~1,5 × la media mensual. Los cortes no se pierden: vuelven como pedido.

### D. SUBIDA FUERTE (> 1,5 × lo esperable en 3M; base 13 %)

| # | Si ves… | Se cumple | Antiguo · reciente · A · B |
|---|---|---|---|
| U2 | **Código irregular que se reactiva:** ha tenido algún mes a cero, los últimos 3M van ≥ 1,2 × su ritmo y su brand no está en campaña de One Shots (< 5 %) | **48 %** [36-61] · 19 cód. | 48 · 48 · 58 · 36 |
| U1 | **Momentum de pedidos:** ≥ 3 pedidos grandes en 12M y últimos 3M ≥ 1,5 × su ritmo | **38 %** [30-48] · 46 cód. | 38 · 38 · 30 · 46 |
| U4 | Recuperación tras cortes: cortes ≥ 0,6 meses de venta y el EPOS de la brand cae ≥ 20 % | 38 % [28-49] · 35 cód. | — · 38 · 28 · 50 |
| U3 | Llenado de canal: el retailer compra ≥ 45 % más de lo que vende y hubo pedido grande en 3 meses | 23 % [18-30] | débil |

**Acción:** con 2+ señales (40 % frente al 10 %), **no recortar**: subir el forecast ~20 % y vigilar el supply.
Al revés que en las caídas, en códigos activos el momentum de pedidos sí continúa.

### E. MES VACÍO el mes que viene (base 26-31 %)

| # | Si ves… | Se cumple |
|---|---|---|
| V1 | **Último mes < 10 % de la media y SIN cortes** → es demanda, no supply | **87 %** [84-90] (87 % en las 4 particiones) |
| V3 | **Último mes < 10 % de la media CON cortes > 1 mes de venta** → es supply | **48 %** vacío y **18 % trae pedido grande** |

**Acción:**
- Mes a cero sin cortes → **forecast 0 el mes siguiente**.
- Mes a cero por cortes → **mantener el forecast y el supply**: la demanda está ahí.

---

## 3. Lo que NO se confirma (también decide)

- **Rebote de un código flojo:** solo el 14 % vuelve a su nivel y **ninguna señal lo anticipa** en las 4 particiones. Acción: no planificar recuperaciones sin un motivo concreto (relanzamiento, promo).
- **Muchos lanzamientos en la brand → muerte de los códigos pequeños:** pasó en el periodo reciente (46 %) pero no en el antiguo (10 %). No es una regla fija.
- **Agotamiento del stock del retailer → pedido:** que el retailer haya vendido lo que compró **no** anuncia el siguiente pedido (con sell-through > 1,8 la probabilidad baja al 7 %). Los pedidos van por calendario: septiembre, octubre, diciembre y marzo.
- **One Shots en general:** no se confirma ninguna combinación. Lo único sólido es que su DA llega ≈ 40 %.

## 4. Otras relaciones medidas sobre lo que pasó de verdad

| Relación | Valor | Acción |
|---|---|---|
| DA positivo planificado frente al sell-in incremental real | **≈ 0,55 por unidad en regulares, ≈ 0,40 en One Shots** | Planificar la mitad del DA como volumen incremental |
| Supply Cut frente al re-pedido en t+1…t+3 | **≈ 0,40 por unidad cortada** (IC 0,22-0,59) | Sumar ~40 % del corte al forecast de los 3 meses siguientes |
| EAN nuevo con el mismo PL y tamaño (sustitución) | El viejo cae a 0 en ~3 meses; el nuevo hereda **~100 %** (relanzamiento: 1,2-2 veces durante el llenado) | Pasar la historia y el forecast del viejo al nuevo |
| Lanzamiento de un regular | El 50 % del primer año entra en los meses 1-3; a los 12 meses el canal tiene 2,4 × lo vendido | No proyectar el mes 1; esperar una recompra débil en los meses 7-12 |
| EPOS de julio-agosto frente al año anterior | Con EPOS < −30 %, la carga de septiembre-noviembre baja (78 %, −22 %) | Dimensionar la carga de Q4 con el EPOS de verano |

---

## 5. Método

- **Indicadores (75)**, todos con información hasta el mes anterior:
  - Sell-in: momentum interanual 1/3/6/12M, aceleración, cruces, volatilidad, *drawdown*, ratio de meses al alza, pendiente, nº de pedidos grandes y meses desde el último, tamaño del mismo mes del año pasado.
  - EPOS: momentum, sell-through, stock en el canal, divergencia sell-in/EPOS, agotamiento desde el último pedido.
  - Grupo: PL, brand y casa sin el propio código, fuerza relativa, cuota en la PL, lanzamientos y One Shots.
  - Otros: cortes, edad, tamaño, segmento y calendario.
- **Búsqueda:** cortes en los percentiles 10/20/30/70/80/90; todas las condiciones sueltas y todas las parejas; los 150 mejores pares se amplían a tríos.
  Se buscó en 4 esquemas: tiempo en los dos sentidos (sin EPOS) y mitades de códigos en los dos sentidos (con EPOS, desde 2024.M10). Confirmación con test binomial y Benjamini-Hochberg.
- **Filtro final:**
  - Supera la base en las 4 particiones: ≥ 2 × la base si la base < 20 %, o ≥ base + 15 pp si es mayor.
  - Tiene ≥ 15 casos por partición y se repite en ≥ 4 meses distintos.
  - Los umbrales se redondearon a valores de negocio y se volvieron a medir.
- **Límites:**
  - Solo Gucci y solo regulares.
  - Las ventanas de meses consecutivos se solapan; por eso se informa del nº de códigos y meses.
  - Las señales con EPOS solo tienen 2024.M10-2026.M08.
  - Correlación ≠ causalidad.
  - Hay que volver a medir cada trimestre y en cada casa.

## Anexo — problemas de datos

| # | Problema | Qué hacer |
|---|---|---|
| D1 | **Cambio de perímetro en la foto 2026.M02**: la historia de actuals sube +29 % (Guilty +69 %). El análisis armoniza las fotos anteriores con un factor por código. | Preguntar qué entró en el export; medir por perímetro en el motor. |
| D2 | Las fotos solo guardan ~8 meses de DAs pasados. | Guardar el DA definitivo de cada mes desde la foto siguiente (t+1). |
| D3 | Las sustituciones de EAN rompen la historia. | Encadenar historias. |
