# Señales de demanda — Gucci, 14 fotos (2025.M09 – 2026.M10)

Análisis exploratorio para la fase de toma de decisiones: qué indicadores anticipan el sell-in futuro y los errores del Consensus.
Datos: `data/Gucci/Consensus/` (14 fotos). Actuals cerrados hasta 2026.M09, EPOS desde 2024.M07.

**Cómo leer la fiabilidad.** "Se cumple X %" es la frecuencia observada, con su intervalo del 95 % (Wilson).
"Base" es lo que pasa sin la señal. La **fuerza** es la diferencia entre ambos:
fuerte = al menos +20 pp y estable en las dos mitades del periodo; media = de +10 a +20 pp; débil = menos de +10 pp, o no se mantiene.
Gucci está en caída (el 68 % de los códigos maduros baja frente al año anterior), así que la base ya es alta.
Una señal solo vale si supera esa base.

---

## 0. Problemas de datos que cambian las conclusiones (leer primero)

| # | Problema | Impacto | Qué hacer |
|---|---|---|---|
| D1 | **Cambio de perímetro en la foto 2026.M02.** Toda la historia de actuals se revisó al alza: +29 % en 2025.H1 y entre +16 % y +126 % según el mes. Por brand: Guilty +69 %, Bloom +25 %, Flora +19 %, Bamboo +97 %. El Consensus futuro también salta (2026.M08: +115 %). El EPOS no cambia. | Las fotos 2025.M09-2026.M01 se miden contra actuals de otro perímetro y parecen infra-forecast. El motor (`actuals_futuros`) usa los actuals de la foto más reciente, así que **la elección de recetas está contaminada**. | Medir cada foto con actuals de su mismo perímetro, o armonizar con un factor por código (actuals nuevos ÷ viejos en los meses que se solapan). Preguntar al equipo qué entró en el perímetro. |
| D2 | **Las fotos solo guardan unos 8 meses de DAs pasados.** El resto aparece como 0. | Con `p` > 0 se limpian los DAs de los meses recientes pero no los del año anterior, así que **el trend sale sesgado** y la base de 12M solo se limpia en parte. | Guardar el DA definitivo de cada mes desde la foto siguiente a ese mes (mes + 1) y montar un histórico propio. |
| D3 | **Sustituciones de EAN** (mismo PL y tamaño, el viejo se apaga en unos 3 meses). | La historia propia del código nuevo empieza de cero y la del viejo cae a 0, así que el trend "Propio" no sirve. | Encadenar el código nuevo con el viejo (ver S11). |
| D4 | El EPOS solo existe desde 2024.M07 y la foto 2025.M11 viene sin EPOS. | El EPOS frente al año anterior solo se puede calcular desde 2025.M07: las señales de EPOS tienen 9-12 meses de prueba. | Repetir el análisis cada trimestre. |

---

## 1. Catálogo de señales

| # | Si ves… | …entonces | Se cumple | Base | Fuerza |
|---|---|---|---|---|---|
| **S1** | **El Consensus asume para los próximos 3 meses un crecimiento interanual más de un 50 % por encima del que muestra el EPOS de los últimos 3 meses** | Sobre-forecast en el SPP3 (SPP3 del grupo **−51 %**) | **81 %** [75-87] · n=167, 47 códigos | 60 % | **Fuerte** (fotos limpias: 83 %) |
| S1b | El Consensus crece entre un 20 % y un 50 % más que el EPOS | Sobre-forecast (SPP3 −10 %) | 70 % [60-79] | 60 % | Media |
| S1c | **El Consensus va alineado con el EPOS (±20 %)** | **SPP3 en meta (+2 %)** | — | — | Fuerte como referencia |
| S1d | El Consensus crece más de un 20 % *menos* que el EPOS | Infra-forecast (SPP3 **+24 %**) | 65 % [57-72] | 40 % | **Fuerte** (fotos limpias: 57 %, base 35 %) |
| **S2** | **El EPOS de los últimos 3 meses cae más de un 30 % frente al año anterior** | El sell-in de los 3 meses siguientes baja frente al año anterior (−22 % agregado) | **79 %** [73-83] · 51 códigos | 68 % | Media (75 % → 82 % entre la primera y la segunda mitad) |
| S2b | El EPOS de los últimos 3 meses estable (±10 %) | Sell-in siguiente +5 % (frente a −22 % con el EPOS hundido) | — | — | Media |
| S2c | Una vez se tiene en cuenta el EPOS frente al año anterior, el sell-in pasado ya no añade información para predecir el sell-in futuro (coeficiente −0,05; p = 0,67) | Para anticipar el sell-in, mirar el EPOS antes que el sell-in | — | — | Media |
| **S3** | **SPP3 ya medido < −30 % y EPOS frente al año anterior < −10 %** | El Consensus vuelve a sobre-forecastear | **78 %** [70-84] · 58 códigos | 67 % | Media (solo fotos limpias: 84 %, n=25, no significativo) |
| S3b | El mismo SPP3 < −30 % pero con el EPOS sin caer | Repite el sobre-forecast | 58 % | 67 % | Ninguna: sin el EPOS, la señal se pierde |
| **S4** | **One Shot con DA ≥ 50 % de la base** | Sobre-forecast ese mes | **82 %** [75-87] | 54 % | **Fuerte** |
| S4b | Regular con DA ≥ 50 % de la base | Sobre-forecast ese mes | 71 % [68-73] | 64 % | Débil |
| **S5** | **DA positivo planificado** | Solo llega una parte: **~0,55 por unidad de DA en regulares** (IC 0,37-0,70) y **~0,40 en One Shots** (IC 0,23-0,52). Fotos limpias, 1-3 meses. | — | — | **Fuerte** (también fuera de muestra, ver §3) |
| S5b | DA negativo | Se cumple ~0,70 (deja infra-forecast) | — | — | Media |
| S5c | El DA de un mes futuro a 1-3 meses vista | El DA definitivo de ese mes será **~2 veces** el planificado: los DAs se cierran tarde | — | — | Media |
| S5d | Tras un mes con DA grande | **No hay resaca** al mes siguiente | — | — | Media (sin efecto) |
| **S6** | **Pedidos grandes** (≥ 2 veces la mediana de 12M) | Van por **calendario**: septiembre 31 %, octubre 25 %, diciembre 21 %, marzo 18 %, frente a 2-3 % en enero, abril y mayo | — | 13 % | Fuerte (patrón) |
| S6b | El retailer vendió mucho de lo que compró | **No** anuncia un pedido grande: con sell-through de 3 meses > 1,8 la probabilidad baja al 7 % | — | 13 % | Fuerte (contraintuitiva) |
| **S7** | **Sell-through de 3 meses > 1,2 y EPOS frente al año anterior < −10 %** (desstockaje) | El mes siguiente el sell-in queda por debajo del 70 % de su media de 12M (de media, 0,51x) | **76 %** [69-81] · 64 códigos | 64 % | Media |
| S7b | Sell-through alto pero EPOS estable | Sell-in normal (0,86x) | — | — | Media |
| **S8** | **EPOS de julio-agosto frente al año anterior < −30 %** | La carga de septiembre-noviembre baja (−22 % agregado) | 78 % · 36 códigos | ~70 % | Media (una sola temporada). Spearman 0,51 frente a 0,36 del sell-in de verano |
| **S9** | **Supply Cut en el mes t** | Vuelve como pedido el **~40 %** (IC 22-59 %) en t+1…t+3, sobre todo en t+1 | — | — | Media. Respalda `c` ≈ 50 % |
| S10 | Lanzamiento de un regular | El 50 % del primer año se envía en los meses 1-3 (mes 1 = 3,7 veces la media de los meses 4-12). A los 12 meses el canal aún tiene sell-in/EPOS = 2,4 (normal: 1,3) | — | — | Media (n=43; 14 con EPOS) |
| S10b | Código en sus meses 7-12 | Consensus SPP −39 % con todas las fotos armonizadas, pero solo −6 % con las fotos limpias. El stock que queda del lanzamiento frenaría la recompra | — | — | Débil (no se mantiene en las fotos limpias) |
| **S11** | **EAN nuevo con el mismo PL, el mismo tamaño y una descripción casi igual** | El viejo cae a 0 en unos 3 meses y el nuevo hereda **~100 %** de su volumen (mediana 1,00). Si es un relanzamiento, 1,2-2,1 veces durante el llenado del canal | 14 de 14 sustituciones claras | — | **Fuerte** |
| S12 | **One Shots en la misma línea** | **Sin canibalismo medible en el EPOS de los regulares** (efecto ≈ 0). En sell-in se mueven juntos porque se cargan en las mismas ventanas (el One Shot del mes *siguiente* "predice" igual) | — | — | Media (confianza en que **no** hay un efecto grande) |
| S13 | Flanker / línea nueva en la brand | Mixto: mediana −6 % en el sell-in del resto de la brand. Bloom Chrysalis −33 %; Gardenia Intense −17 % en sell-in y +12 % en EPOS; Ambrosia d'Oro +46 % | ~50 % | — | **Débil**: no usar |
| S14 | Revisión de la base del Consensus frente a la foto anterior | Recortes > 30 % se pasan (SPP +19 %); el resto no anticipa nada | — | — | Débil |

---

## 2. Ajuste manual frente a System FC + DA (valor añadido del forecaster, regulares, 1-3 meses)

| Grupo | WAPE Consensus | WAPE Sys+DA | Mejora del ajuste manual |
|---|---|---|---|
| Año 1, meses 1-6 | 57 % | 126 % | **+69 pp** |
| Año 1, meses 7-12 | 69 % | 115 % | **+46 pp** |
| Año 2 | 63 % | 65 % | +2 pp |
| Año 3+ | 55 % | 58 % | +3 pp |

(fotos limpias 2026.M02-M06)

En los códigos maduros el ajuste manual aporta 1-3 pp de WAPE. En los nuevos y en los que tienen flag 1/2 aporta mucho.
En los **Bulls** el Consensus sobre-forecastea un −27 %, más que el sistema (−18 %): ahí el ajuste empeora el bias.

---

## 3. Lo más importante para la toma de decisiones: las recetas fuera de muestra

Prueba hecha como en la vida real: en cada foto F se elige la receta solo con los tramos ya cerrados antes de F y se mide en F+1…F+3.
Son 6 fotos de prueba (2026.M01-M06), con el perímetro armonizado.

| Estrategia | WAPE90 | Gana al Consensus |
|---|---|---|
| Consensus | **56,1 %** | — |
| Receta propia por código (oráculo de las fotos pasadas) | 83,2 % | 0/6 |
| Regla por Product Line / Edad / Segmento / Casa | 73-74 % | 0/6 |
| Mezcla 25 % receta + 75 % Consensus | 55,6-55,9 % | marginal |
| Oráculo ex post (inalcanzable) | 27,3 % | 6/6 |
| **Consensus con el DA recortado** (calibrado con fotos pasadas, bias neutro) | Regular 58,3 → 56,1 % · **One Shot 103 → 94 %** (SPP −22 % → −2 %) | 4/8 · **6/8** |

Conclusiones:
1. **Elegir la mejor de 75.816 recetas por código se ajusta al ruido** (83 % fuera de muestra frente al 27 % dentro). La receta ganadora cambia de una foto a otra.
2. Ni la mejor receta fija elegida a posteriori gana al Consensus en 2026. De media en las 10 fotos queda en 69,8 % frente a 71,1 %, pero pierde en todas las fotos de 2026.M02 a 2026.M06.
3. La regla de Casa que sale con datos pasados es estable: estacionalidad completa de House a 2 años, `w` = 1, **`m` = 1 (trend de sell-out)**, N = 6, `p` = 1. Que salga el trend de EPOS cuadra con S1-S2.
4. **El valor está en corregir el Consensus con señales** (DA real, brecha frente al EPOS, desstockaje), no en sustituirlo.
   El detector debería avisar por **señales** (S1, S3, S4, S7), no por distancia a una receta que no gana fuera de muestra.

---

## 4. Propuestas para el motor (por decidir con el equipo)

1. **Medir por perímetro** (D1) y volver a calcular el cubo. Hecho en el análisis con un factor por código; habría que pasarlo al pipeline.
2. **Factor de realización de DAs** en la configuración: `rho_DA` ≈ 0,55 en regulares y 0,40 en One Shots, en lugar de respetarlos al 100 %. Choca con la decisión actual del usuario ("los DAs se respetan al 100 %"): **pregunta abierta**.
3. **Histórico de DAs** guardado desde la foto t+1 (D2) antes de usar `p` > 0.
4. **Encadenar sustituciones de EAN** (S11).
5. **Regla por grupo con contracción**: si se elige receta, que sea por grupo y solo cuando gane al Consensus en las fotos de validación; si no, no proponer cambio.
6. **Detector de señales**: brecha Consensus/EPOS > 50 %, DA dominante en One Shots, SPP3 < −30 % con EPOS cayendo y sell-through alto con EPOS cayendo.
7. **Indicador de la carga de Q4**: EPOS de julio-agosto frente al año anterior → tamaño de la carga de septiembre-noviembre (S8).

---

## 5. Método y límites

- La verdad de cada mes sale de la foto más reciente que lo trae (comprobado contra los CSV: actuals, EPOS, DA y Consensus cuadran exactamente).
  El EPOS no se revisa entre fotos.
- Las señales de Consensus se repitieron de tres formas: todas las fotos, solo fotos limpias (≥ 2026.M02) y fotos armonizadas. Las cifras de la tabla son las armonizadas, con la versión limpia al lado.
- Comprobaciones de robustez: primera y segunda mitad del periodo; muestra sin ventanas solapadas (una foto por trimestre); nº de códigos distintos; % de códigos donde la señal acierta más de la mitad de las veces; test de Fisher.
  Se miraron ~20 hipótesis: con esa cantidad, una con p ≈ 0,05 puede salir por azar. Las fuertes tienen p < 1e-6.
- Correlación no es causalidad. S12 y S13 en especial: los One Shots y los regulares se cargan en las mismas campañas.
- Muestra corta: 10 fotos con SPP3 cerrado (5 limpias) y 27 meses de EPOS. Las fiabilidades pueden moverse ±10 pp con más fotos.
- La WAPE es mensual por código (Σ|F−A| / ΣA), como define el equipo.
