# Señales del Consensus — Gucci, 14 fotos (2025.M09 – 2026.M10)

**Pregunta:** ¿qué combinación de indicadores, visible el día de la foto, anticipa que el Consensus de los próximos 3 meses va a fallar por más de un 30 %?
**Método:** minería sistemática con confirmación fuera de muestra, no hipótesis hechas a mano (ver §5).

- Población: regulares con Consensus ≥ 60 uds en los 3 meses siguientes.
- 1.324 casos código × foto: 10 fotos medidas (5 de 2025, 5 de 2026) y unos 145 códigos.
- **Sobre-forecast** = actual < 0,7 × Consensus en F+1…F+3. Base: 43-48 %.
- **Infra-forecast** = actual > 1,3 × Consensus. Base: 17-24 %.

---

## 1. El scorecard (regulares)

Se suman los puntos de las condiciones que se cumplen. Los puntos se calibraron con las fotos de 2025 y las probabilidades son las **observadas en las fotos de 2026**, que el modelo no vio.

### Indicadores (todos se calculan con lo que se sabe el día de la foto)

| Indicador | Cálculo |
|---|---|
| **Cons/ritmo** | Consensus de los meses 1-3 ÷ (sell-in de los últimos 12 meses ÷ 4) |
| **Forma del Consensus** | Consensus de los meses 7-9 ÷ Consensus de los meses 1-3 |
| **Peso del DA** | Total Demand Assumption de los meses 1-3 ÷ Consensus de los meses 1-3 |
| **Consensus frente al EPOS** | (Consensus 3M ÷ sell-in de esos meses el año pasado) ÷ (EPOS de los últimos 3M ÷ EPOS de esos meses el año pasado) |
| **Cortes** | Supply Cuts de los últimos 3 meses ÷ sell-in medio mensual de 12M |
| **Último mes** | Sell-in del último mes cerrado ÷ media mensual de 12M |
| **One Shots en la PL** | Sell-in de los One Shots de su Product Line en los últimos 3M ÷ sell-in regular de la PL |

### A. Riesgo de SOBRE-forecast (AUC 0,74 en 2026; 0,81 con los periodos invertidos)

| Puntos | Condición |
|---|---|
| +14 | DA > 40 % del Consensus |
| +11 | El Consensus crece más de un 50 % por encima de lo que crece el EPOS |
| +3 | Cons/ritmo > 2x |
| +3 | Consensus cargado al inicio (meses 7-9 < 0,5 × meses 1-3) |
| +3 | Último mes ≈ 0 (< 15 % de la media) |
| +1 | Cons/ritmo 1,25-2x |
| −1 | Último mes > 1,5 × la media |
| −2 | Cortes > 0,5 meses de venta |
| −2 | El Consensus crece más de un 20 % por debajo de lo que crece el EPOS |
| −5 | DA negativo |
| −6 | Cons/ritmo 0,5-0,8x |
| −7 | Cortes > 2 meses de venta |
| −10 | Cons/ritmo < 0,5x |
| −11 | One Shots > 40 % del regular de su PL |

| Puntos | % con sobre-forecast >30 % (2026) | Mediana actual/Consensus |
|---|---|---|
| ≤ −10 | 21 % [16-28] · n=169, 69 códigos | 1,03 |
| −9 a 0 | 41 % [33-50] | 0,81 |
| 1 a 10 | 47 % [38-56] | 0,72 |
| **11 a 20** | **78 % [67-86]** · n=68, 41 códigos | **0,24** |
| **> 20** | **82 % [66-92]** · n=34, 17 códigos | **0,23** |

### B. Riesgo de INFRA-forecast (AUC 0,73 en 2026; 0,78 con los periodos invertidos)

| Puntos | Condición |
|---|---|
| +12 | Cons/ritmo < 0,5x |
| +11 | Cortes > 2 meses de venta |
| +5 | Cortes > 0,5 meses de venta |
| +3 | Cons/ritmo 0,5-0,8x |
| +3 | One Shots > 40 % en su PL |
| +2 | Último mes ≈ 0 |
| +2 | Último mes > 1,5 × la media |
| +1 | El Consensus espera recuperación (meses 7-9 > 2 × meses 1-3) |
| +1 | El Consensus crece más de un 20 % por debajo del EPOS |
| −1 | Cons/ritmo > 2x |
| −3 | DA negativo |
| −8 | Cons/ritmo 1,25-2x |
| −9 | El Consensus crece más de un 50 % por encima del EPOS |
| −14 | Consensus cargado al inicio |
| −16 | DA > 40 % del Consensus |

| Puntos | % con infra-forecast >30 % (2026) | Mediana actual/Consensus |
|---|---|---|
| ≤ −10 | 7 % [4-13] | 0,41 |
| −9 a 0 | 8 % [4-13] | 0,76 |
| 1 a 8 | 22 % [17-30] | 0,92 |
| 9 a 15 | 30 % [19-43] | 1,07 |
| **> 15** | **69 % [50-83]** · n=26, 16 códigos | **1,68** |

**Lectura:** con 11 puntos o más de sobre-forecast, **4 de cada 5 códigos venden menos del 70 % de su Consensus**, y el código típico vende la cuarta parte.

**Efecto en el KPI:** corregir a medias según la puntuación (factor por tramo de puntos y tamaño del código) deja el SPP3 de 2026 en +3 % (el Consensus estaba en −8,5 %) sin empeorar el WAPE.
Aplicado al revés (calibrar en 2026, probar en 2025) baja el WAPE3 del 67 % al 57 %.
El riesgo se concentra en códigos pequeños y medianos: en volumen el impacto es menor que en número de códigos.

---

## 2. Patrones confirmados

Cada combinación se descubrió en un periodo y se confirmó en el otro, con FDR < 5 %, al menos 8 códigos distintos y ≥ +10 pp sobre la base.
"%" = acierto en el periodo de confirmación. "A/C" = mediana actual/Consensus en ese periodo.

### Sobre-forecast (base 43-48 %)

| # | Patrón | Descubierto → confirmado | % | A/C |
|---|---|---|---|---|
| P1 | **Rabbit con Cons/ritmo ≥ 1,6x** | 87 % → **85 %** (n=96, 30 cód.) | 85 % | 0,10 |
| P2 | **Código que crece ≥ 45 % menos que su PL** (sell-in YoY 3M) **y Cons/ritmo ≥ 2,9x** | 100 % → **95 %** (n=19, 9 cód.) | 95 % | 0,04 |
| P3 | **Pierde cuota en su PL** (cuota 3M < 0,77 × cuota 12M), **sin cortes, y Cons/ritmo ≥ 1,2x** | 97 % → **90 %** (n=30, 20 cód.) | 90 % | 0,10 |
| P4 | **Canibalismo:** la brand lanzó en 6 meses ≥ 38 % de su volumen regular, **el código ya está parado** (último mes < 23 % de la media) **y sin cortes** | 96 % → **92 %** (n=12, 12 cód.) | 92 % | 0,07 |
| P5 | **Desaceleración:** YoY 3M ≤ 0,36 × YoY 12M **y Cons/ritmo ≥ 1,7x** | 94 % → **89 %** (n=18, 10 cód.) | 89 % | 0,09 |
| P6 | Código débil (YoY 6M < −30 %), por debajo de su brand, y Consensus que asume ≥ 2,4 veces el crecimiento del EPOS | 97 % → **89 %** (n=19, 13 cód.) | 89 % | 0,13 |
| P7 | Consensus que es casi todo DA (DA ≥ Consensus) y cargado al inicio | 86 % → **90 %** (n=20, 8 cód.) | 90 % | 0,00 |
| P8 | **Tamaño ≥ 100 ml con DA ≥ 26 % del Consensus** | 85 % → **75 %** (n=56, 20 cód.) | 75 % | 0,10 |
| P9 | El Consensus asume ≥ 6 veces el crecimiento reciente del sell-in, con la brand estable o creciendo | 90 % → **87 %** (n=31, 13 cód.) | 87 % | 0,25 |

### Infra-forecast (base 17-24 %)

| # | Patrón | Descubierto → confirmado | % | A/C |
|---|---|---|---|---|
| Q1 | **Cortes recientes (≥ 0,25 meses de venta) y Consensus recortado por debajo del ritmo (< 0,67x) y del año pasado (< 0,82x)** | 73 % → **87 %** (n=15, 9 cód.) | 87 % | 2,02 |
| Q2 | **Consensus recortado ≥ 37 % frente a hace 3 fotos y sin crecer más que el EPOS** | 48 % → **80 %** (n=35, 29 cód.) | 80 % | 2,00 |
| Q3 | **Últimos 3 meses en máximos de 12M (≥ 93 % del mejor trimestre) y Consensus < 0,55x del ritmo** | 74 % → **79 %** (n=14, 8 cód.) | 79 % | 1,78 |
| Q4 | Consensus < 0,67x del ritmo, por debajo del EPOS y con DA negativo ≥ 30 % | 76 % → **71 %** (n=28, 20 cód.) | 71 % | 1,73 |
| Q5 | **Cortes recientes y Consensus que espera recuperación tardía** (meses 7-9 ≥ 2,2 × meses 1-3) | 56 % → **71 %** (n=21, 19 cód.) | 71 % | 1,64 |
| Q6 | EPOS sin caer (YoY ≥ −12 %) y Consensus < 0,70x del ritmo | 44 % → **69 %** (n=36, 22 cód.) | 69 % | 1,53 |

### Confluencia

Se eligieron 8 señales mirando solo el periodo de descubrimiento y se contaron las activas en el otro:

| Señales activas | Sobre-forecast 3M | Infra-forecast 3M |
|---|---|---|
| 0 | 39 % | 13 % |
| 1 | 61 % | 21 % |
| 2 | 68 % | 46 % |
| **3+** | **91 %** (A/C 0,34) | **82 %** (A/C 1,39) |

### Las tres ideas que hay detrás

1. **El Consensus no se cree el declive.** Si el código pierde contra su PL, su brand o su propio ritmo (P2, P3, P5, P6) y el Consensus no baja, el actual se queda muy por debajo.
2. **El Consensus se pasa al recortar después de un corte.** Los cortes deprimen los actuals; el Consensus recorta por debajo del ritmo; cuando vuelve el supply, el actual sale 1,6-2 veces por encima (Q1, Q2, Q5).
3. **El DA en tallas grandes, o encima de un código parado, no llega** (P4, P7, P8).

---

## 3. Lo que no funciona (también es información)

- **One Shots:** ninguna combinación se confirma. Se sobre-forecastean el 50-67 % de las veces pase lo que pase. Lo único robusto es recortar su DA: llega ≈ 40 %.
- **Horizonte de 1 mes:** las reglas se ajustan al ruido (100 % en descubrimiento, ~50 % en validación) y el modelo tiene un AUC de 0,57-0,62. No sirve.
- **Patrones de demanda sin el Consensus** (subida o caída interanual del sell-in): salen, pero son obvios ("si lleva 12 meses cayendo, sigue cayendo") y no aportan nada que no se vea mirando la serie.
- **Revisiones entre fotos y fuerza relativa frente a la PL** como indicadores sueltos: inestables entre periodos. Solo valen combinados, como en Q2 y P2.

---

## 4. Cómo usarlo

1. Calcular los 7 indicadores en cada foto (el pipeline ya tiene todos los datos) y mostrar los dos puntajes por código como semáforo de riesgo.
2. Revisar primero los códigos con ≥ 11 puntos de sobre-forecast o > 15 de infra-forecast. En 2026 eran el 25 % de los casos: fallan más de un 30 % en el **83 %** de las veces, frente al 54 % del resto, y recogen un tercio de todos los fallos. Es una lista de prioridades, no un detector completo.
3. En el detector, avisar por patrón (P1-P9, Q1-Q6) con su probabilidad, en lugar de por distancia a una receta.
4. Volver a calibrar los puntos cada trimestre con las fotos nuevas. Con 10 fotos medidas, los porcentajes pueden moverse ±10 pp.

---

## 5. Método y validación

- **Biblioteca de indicadores:** 62 de análisis técnico calculados solo con información ≤ F−1 (momentum interanual 1/3/6/12M, aceleración, cruces de medias, volatilidad, *drawdown*, ratio de meses al alza, pendiente, meses desde el último pedido grande, EPOS, sell-through, stock en el canal, divergencia sell-in/EPOS, PL/brand/casa sin el propio código, fuerza relativa, cuota en la PL, lanzamientos y One Shots en el grupo, cortes, edad, tamaño, segmento y calendario).
  Más 13 indicadores de la propia foto: Consensus frente al ritmo, al año pasado, al EPOS y al sell-in; peso del DA; ajuste manual frente a Sistema + DA; capas Initiative/Prometheus; revisiones a 1 y 3 fotos; forma de la curva.
- **Minería:** cada indicador se corta en los percentiles 10/20/30/70/80/90. Se prueban todas las condiciones sueltas y todas las parejas (~200.000), los 150 mejores pares se amplían a tríos y se ordenan por la cota inferior de Wilson.
- **Confirmación:** en el otro periodo, test binomial contra su tasa base, corrección Benjamini-Hochberg, al menos 8 códigos distintos y ≥ +10 pp. Se minó en las dos direcciones del tiempo (2025 → 2026 y 2026 → 2025).
- **Scorecard:** logística regularizada sobre los indicadores en tramos con umbrales redondos, calibrada en 2025 y medida en 2026. También al revés.
- **Perímetro:** las fotos 2025.M09-2026.M01 son de un perímetro más pequeño. Se armonizaron con un factor por código (actuals nuevos ÷ viejos en 2024-2025) y se excluyeron 23 códigos que casi solo existen en el perímetro nuevo.
- **Límites:**
  - Las ventanas de fotos consecutivas se solapan; por eso se exigen códigos distintos y se informa de los IC.
  - Los patrones con n < 25 son prometedores pero frágiles.
  - Correlación ≠ causalidad.
  - Solo hay datos de Gucci: hay que repetirlo en cada casa.

## Anexo — problemas de datos encontrados

| # | Problema | Qué hacer |
|---|---|---|
| D1 | **Cambio de perímetro en la foto 2026.M02**: la historia de actuals sube +29 % (Guilty +69 %, Bloom +25 %, Flora +19 %) y el Consensus futuro salta hasta +115 %. El EPOS no cambia. El motor mide las fotos viejas contra actuals del perímetro nuevo. | Medir por perímetro o armonizar con un factor por código. Preguntar qué entró en el export. |
| D2 | Las fotos solo guardan **~8 meses de DAs pasados**: con `p` > 0 la limpieza es asimétrica y sesga el trend. | Guardar el DA definitivo de cada mes desde la foto siguiente (t+1). |
| D3 | **Sustituciones de EAN** (mismo PL y tamaño): el viejo cae a 0 y el nuevo hereda ~100 %. | Encadenar historias. |
| D4 | DAs: llega ≈ 55 % en regulares y ≈ 40 % en One Shots. | Factor de realización configurable (decisión abierta). |
| D5 | Las recetas del motor elegidas con fotos pasadas no ganan al Consensus fuera de muestra (73-83 % frente a 56 % de WAPE90). | Usar las señales para corregir o priorizar el Consensus, no para sustituirlo. |
