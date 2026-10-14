---
name: Brújulas de Demand
description: Oráculo retrospectivo de recetas de forecast por código y foto, con detector de desvíos del Consensus.
colors:
  ink: "#141414"
  paper: "#ffffff"
  canvas: "#f5f5f5"
  mist: "#e9e9e9"
  hairline: "#d9d9d9"
  grid: "#e4e4e4"
  mute: "#5c5c5c"
  mute-2: "#8a8a8a"
  consensus-gray: "#7a7a7a"
  highlight-yellow: "#fecc33"
  ember: "#ff8400"
  ember-ink: "#b45400"
  forest: "#21935b"
  ok-green: "#16703f"
  dev-inside: "#d6d6d6"
  dev-low: "#b3b3b3"
  dev-mid: "#ffb366"
  dev-high: "#ff8400"
  dev-extreme: "#141414"
  ink-dark: "#f0f0ee"
  paper-dark: "#1b1b1b"
  canvas-dark: "#111111"
  mist-dark: "#262626"
  hairline-dark: "#333333"
  grid-dark: "#1c1c1c"
  mute-dark: "#a9a9a9"
  ember-ink-dark: "#ff9a33"
  ok-green-dark: "#4cc985"
typography:
  display:
    fontFamily: "Schibsted Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(44px, 6.4vw, 92px)"
    fontWeight: 500
    lineHeight: 0.86
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Schibsted Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(32px, 4.4vw, 47px)"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Schibsted Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title-sm:
    fontFamily: "Schibsted Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "27px"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  card-title:
    fontFamily: "Schibsted Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 500
    lineHeight: "24px"
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Arial, Helvetica Neue, Helvetica, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.4
  body-sm:
    fontFamily: "Arial, Helvetica Neue, Helvetica, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.06em"
  chart-label:
    fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "9.5px"
    fontWeight: 400
    letterSpacing: "0.04em"
rounded:
  link: "4px"
  cell: "6px"
  btn: "8px"
  card: "16px"
  marker: "25px"
  pill: "160px"
spacing:
  "4": "4px"
  "8": "8px"
  "12": "12px"
  "16": "16px"
  "20": "20px"
  "24": "24px"
  "32": "32px"
  "40": "40px"
  "56": "56px"
  "80": "80px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.btn}"
    padding: "10px 16px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.btn}"
    padding: "10px 16px"
  chip:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "8px 12px"
  chip-pressed:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  search-pill:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "8px 8px 8px 22px"
  select-pill:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "9px 34px 9px 16px"
  panel:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.card}"
    padding: "20px"
  compass-card:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.card}"
    padding: "16px"
    width: "360px"
    height: "480px"
  result-card:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.card}"
    padding: "16px"
    width: "360px"
    height: "410px"
  tooltip:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.btn}"
    padding: "10px 12px"
  marker:
    backgroundColor: "{colors.highlight-yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.marker}"
---

# Design System: Brújulas de Demand

## Overview

**Creative North Star: "La mesa de trabajo del planner"**

Brújulas de Demand se presenta como un cuaderno de ingeniería sobre una mesa: un lienzo gris claro cuadriculado (rejilla de 40 px) donde se apoyan, sin flotar, paneles blancos de esquinas suaves con un filete de pelo. Todo es tinta casi negra sobre papel. El color aparece solo cuando significa algo: el naranja brasa marca lo que se sale de la estrategia, el verde marca la zona meta y el amarillo rotulador señala lo elegido. El mundo viene fijado por la guía de estilo del usuario (`DESIGN html.md`, referencia "Flim"), adaptada a una herramienta de operación con densidad de datos alta.

La superficie es de **operación**, no de escaparate: filtrar primero, leer después. La portada combina una cabecera con el nombre a gran escala, un buscador en píldora, filas de chips de filtro y un mapa de burbujas anidadas (casa → brand → product line → EAN) junto a un panel lateral fijo con la lista ordenada. El detalle de un código apila secciones (Foto actual, Decisiones, Resultados, Detector) con un rail de resumen pegajoso a partir de 1280 px. Los números van en mono o con cifras tabulares; los gráficos son SVG dibujados a mano con la misma tinta y los mismos grises que el texto.

Hay tema claro y oscuro con selector manual (Claro / Oscuro / Auto); el oscuro invierte la tinta y el papel y conserva la cuadrícula y los acentos funcionales.

**Key Characteristics:**
- Lienzo cuadriculado como superficie de toda la página, nunca como adorno de un bloque.
- Monocromo de tinta: el color es señal (desvío, meta, elección), nunca decoración.
- Tres voces tipográficas: grotesca de display, mono de etiquetas en mayúsculas, Arial para leer.
- Tres radios estructurales (8 / 16 / 160 px) y cero sombras.
- Tarjetas de brújula de tamaño fijo en px, alineadas en rejilla 2 × 2.

## Colors

Monocromo de tinta sobre papel gris con tres acentos funcionales escasos.

### Primary
- **Tinta** (ink): texto, iconos de trazo fino, botón relleno, chips pulsados, tooltip, trayectoria y línea de la receta en los gráficos, y el escalón extremo del desvío. Es la única "marca" del sistema.

### Secondary
- **Brasa** (ember): lo que se sale de la estrategia. Puntos de mes fuera de rango en el gráfico de la foto actual, escalón 15–30 % del mapa, punto del logotipo.
- **Brasa tinta** (ember-ink): versión legible de la brasa para texto (desvíos en la tabla del detector, avisos, valores "malo"). En oscuro se aclara (ember-ink-dark).

### Tertiary
- **Amarillo rotulador** (highlight-yellow): marcador detrás de palabras (`marcador`), celda elegida del selector, contorno de la burbuja activa y selección de texto. Siempre con texto en tinta clara fija (#141414).
- **Bosque** (forest) y **Verde OK** (ok-green): línea discontinua de WAPE 40 % en las medias brújulas y valores dentro de meta ("bueno"). La zona meta se rellena con verde señal al 12 % (18 % en oscuro).

### Neutral
- **Lienzo** (canvas): fondo de página bajo la cuadrícula.
- **Rejilla** (grid): líneas de 1 px de la cuadrícula del lienzo.
- **Papel** (paper): paneles, tarjetas, chips, buscador; texto sobre tinta.
- **Niebla** (mist): fila activa de la lista, separadores interiores de tabla y del rail.
- **Filete** (hairline): bordes de 1 px de paneles, chips, inputs y burbujas.
- **Gris apagado** (mute, mute-2): textos secundarios, cabeceras de tabla, etiquetas de eje, separadores de migas.
- **Gris Consensus** (consensus-gray): la serie "lo que pasó" (Consensus real), siempre discontinua 4/3.

### Escala de desvío del mapa
Cinco escalones de relleno para las burbujas EAN según el desvío en %: Dentro (dev-inside), hasta 5 % (dev-low), 5–15 % (dev-mid), 15–30 % (dev-high = brasa) y más de 30 % (dev-extreme = tinta). Cada escalón tiene su color de etiqueta propio para mantener el contraste, y la leyenda los nombra en texto.

### Named Rules
**La regla de la señal.** Ningún color que no sea neutro aparece sin significado de dato: brasa = fuera de estrategia, verde = meta, amarillo = elegido. Si un elemento no comunica uno de esos tres estados, va en tinta o gris.

**La regla de la doble pista.** El color nunca es la única señal: cada desvío lleva su cifra, su tooltip o su texto de leyenda; el Consensus además se distingue por el trazo discontinuo.

**La regla del amarillo sin superficie.** El amarillo marca palabras o una celda elegida; no rellena paneles ni tarjetas.

## Typography

**Display Font:** Schibsted Grotesk 500/600 (con ui-sans-serif, system-ui)
**Body Font:** Arial (con Helvetica Neue, Helvetica)
**Label/Mono Font:** JetBrains Mono 400/500 (con ui-monospace, SFMono-Regular, Menlo)

**Character:** una grotesca de peso medio a gran escala y con interletraje cerrado da el tono de herramienta seria; la mono en mayúsculas con 0,06em convierte cada etiqueta en una anotación de plano; Arial lee sin pretender nada.

### Hierarchy
- **Display** (500, clamp 44–92 px, 0.86, −0.02em): solo el nombre "Brújulas de Demand" en la cabecera de la portada.
- **Headline** (500, clamp 32–47 px, 1.0): título del código en el detalle; cifra grande del rail (47 px).
- **Title** (500, 32 px, 1.1): títulos de sección del detalle (Decisiones, Resultados, Detector).
- **Title-sm** (500, 27 px): título del panel lateral, cifras de la cabecera y del rail. Las cifras KPI de la ficha van a 21 px.
- **Card title** (500, 17 px, altura fija 24 px, una línea con elipsis): títulos de tarjeta de brújula y de resultado.
- **Body** (400, 16 px, 1.4): texto base. El claim de la cabecera sube a 20 px; resúmenes a 15 px; info del detalle a 14 px con 1.6 y máx. 110ch.
- **Body-sm** (400, 13 px): tablas, tooltip, notas; subtítulos y pies de tarjeta a 12,5 px.
- **Label** (mono 400, 12 px, 0.06em, MAYÚSCULAS, 1.0): navegación, chips, botones, selectores, migas, cabeceras de tabla (11 px), etiquetas de grupo de filtros, placeholder del buscador (15 px).
- **Chart label** (mono 400, 9,5 px, 0.04em, MAYÚSCULAS, gris apagado): todo texto dentro de SVG.

### Named Rules
**La regla de las tres voces.** Display para nombres y cifras, mono para etiquetas y controles, Arial para frases. No se introduce una cuarta familia.

**La regla de la cifra tabular.** Toda cifra comparable (tablas, lista, KPIs) usa cifras tabulares o mono para que las columnas se alineen.

## Layout

- **Lienzo completo:** sin contenedor central; la página ocupa todo el ancho con márgenes laterales de 32 px (16 px en móvil). Barra superior de 64 px, no fija.
- **Portada ("mesa"):** rejilla de dos columnas, mapa flexible + panel de 400 px, separación 32 px. El lienzo del mapa es cuadrado, máx. `min(880px, 100dvh − 96px)`, alineado a la derecha de su columna. El panel es pegajoso (top 16 px) y su lista hace scroll interno con un fundido de 28 px al pie. Bajo 1100 px pasa a una columna.
- **Detalle:** secciones separadas 56 px; contenedores anchos ("ancho") en papel con 20 px de relleno y scroll horizontal propio para tablas. A partir de 1280 px aparece el rail de resumen de 300 px pegajoso a la derecha; por debajo sube arriba del contenido.
- **Rejilla de brújulas:** 2 columnas fijas de 360 px con 24 px de hueco; una columna bajo 820 px; centrada a ancho completo en móvil (máx. 360 px).
- **Ritmo:** base de 4 px; pasos más usados 8 / 12 / 16 / 20 / 24 / 32, secciones a 56 y pie a 80.
- **Móvil (≤ 700 px):** la navegación se oculta, la barra envuelve, las filas de chips hacen scroll horizontal con fundido a la derecha y las cifras de cabecera pasan a rejilla de 3.

**La regla del tamaño fijo.** Las cuatro tarjetas de cada rejilla 2 × 2 tienen exactamente el mismo tamaño en px (360 × 480 para Decisiones, 360 × 410 para Resultados), con lienzo SVG fijo (326 × 326 y 326 × 230) y título de altura fija. Nunca se dimensionan por contenido.

## Elevation & Depth

Sistema plano: no hay `box-shadow` de elevación. La profundidad sale del contraste lienzo / papel (gris sobre blanco), del filete de 1 px y del radio de 16 px, que hace que los paneles parezcan apoyados en la mesa. La capa superior (tooltip, enlace "Saltar al contenido") se distingue por invertirse a tinta, no por sombra. En los gráficos, la jerarquía es de opacidad: la trayectoria de una brújula atenúa los puntos antiguos y agranda el último.

**La regla del papel apoyado.** Ninguna superficie flota. Si algo debe destacar, se invierte a tinta o se le cambia el filete a tinta (ficha del código seleccionado, buscador con foco), nunca se le añade sombra.

## Shapes

Tres radios estructurales y dos de detalle:
- **Botón** (8 px): botones, inputs numéricos y selects de controles, tooltip, filas de lista.
- **Tarjeta** (16 px): paneles, tarjetas de brújula, lienzo del mapa, ficha, rail.
- **Píldora** (160 px): buscador, chips, selector de casa, selector de tema, etiquetas de grupo del mapa.
- **Detalle:** 4 px para foco y teclas (`⌘K`), 6 px para las celdas de la matriz del selector, 25 px para el marcador amarillo.

Bordes siempre de 1 px en filete; el único borde en tinta es el estado de foco o selección. Las burbujas del mapa son círculos con trazo que no escala (`vector-effect: non-scaling-stroke`). Los iconos son SVG de trazo fino de 1,5 px en `currentColor`.

## Components

### Buttons
- **Shape:** esquinas suaves (8 px).
- **Primary:** relleno de tinta, texto en papel, etiqueta mono, 10 × 16 px. Es el único botón relleno (p. ej. "Buscar").
- **Ghost:** transparente con filete y texto en tinta.
- **Enlace:** botón de texto subrayado con subrayado en filete que pasa a tinta al pasar el ratón.
- **Estados:** al pulsar escala a 0,97 (160 ms, ease-out); deshabilitado al 35 % de opacidad. Foco visible: contorno de 2 px en tinta con 2 px de separación.

### Chips
- **Style:** píldora en papel con filete, etiqueta mono, 8 × 12 px.
- **State:** pulsado (`aria-pressed`) se invierte a tinta con texto en papel; al pasar el ratón el filete pasa a tinta. Agrupados con una etiqueta mono gris delante (Scope, Estado, Segmento, Edad, Tolerancia).

### Cards / Containers
- **Corner Style:** 16 px.
- **Background:** papel sobre el lienzo cuadriculado.
- **Shadow Strategy:** ninguna (ver Elevation & Depth).
- **Border:** filete de 1 px; la ficha del código seleccionado usa filete en tinta.
- **Internal Padding:** 20 px en panel, rail y contenedores anchos; 16 px en tarjetas de brújula y ficha.

### Inputs / Fields
- **Buscador:** píldora en papel con filete, icono de lupa a la izquierda, texto mono 15 px con placeholder en mayúsculas y botón primario acoplado a la derecha. Con foco, el filete pasa a tinta.
- **Numéricos y selects:** radio de 8 px, filete, mono 12 px alineado a la derecha para tolerancias. Casillas con `accent-color` en tinta.
- **Selector de casa:** píldora mono con flecha dibujada por gradiente.

### Navigation
- Enlaces mono sin fondo al 55 % de opacidad; el activo al 100 % con subrayado de 1 px a 6 px. Selector de tema segmentado en píldora: la opción activa se rellena de tinta. Migas mono en gris con el nivel actual en tinta. En móvil la navegación se oculta y se navega por el mapa y el botón "Volver al mapa".

### Tooltip
Bloque en tinta con texto en papel, 8 px de radio, 13 px, ancho máx. 300 px, con una línea mono atenuada de cabecera. Aparece con un fundido de 120 ms.

### Mapa de burbujas (signature)
Empaquetado circular anidado casa → brand → product line → EAN dentro de un lienzo cuadrado de 16 px. Brands en papel y product lines en papel tenue, ambos con filete; las hojas EAN se rellenan con la escala de desvío. EAN sin dato: hueco con trazo gris; sin receta: trazo discontinuo 2/2. Lo no filtrado baja al 12 %; la burbuja activa lleva contorno amarillo de 3 px. El zoom entre niveles anima la transformación del grupo (560 ms, ease-in-out); las etiquetas de grupo son píldoras mono con su recuento.

### Brújula (signature)
Tarjeta fija de 360 × 480 con lienzo SVG de 326 px. Polos de cada eje en sus extremos, ejes y rótulos en mono gris de 9,5 px. La trayectoria del código es una polilínea en tinta al 45 % con un punto por foto (5 px; el último 9 px), los antiguos más tenues, con borde en papel.

### Media brújula de resultados (signature)
Tarjeta de 360 × 410 con lienzo de 326 × 230. Zona meta rellena en verde translúcido y línea discontinua de WAPE 40 % en bosque. Dos series: Consensus real en gris discontinuo 4/3 y receta en tinta continua.

### Matriz del selector
Tabla de 17 celdas de 42 px de alto con radio de 6 px; más tinta = grupo más grande. La celda elegida se rellena de amarillo con un anillo interior de 2 px en tinta.

### Tablas
Cabeceras mono gris de 11 px en mayúsculas, celdas a 13 px con cifras tabulares, alineadas a la derecha salvo descripciones; separadores de niebla. Las columnas ordenables pasan a tinta al pasar el ratón; los desvíos fuera de estrategia van en brasa tinta y negrita.

## Do's and Don'ts

### Do:
- **Do** apoyar toda la página sobre el lienzo (canvas) con la cuadrícula de 40 px en líneas de 1 px (grid).
- **Do** usar solo los radios 8 / 16 / 160 px para botones, tarjetas y píldoras, y reservar 4 / 6 / 25 px a foco, celdas de matriz y marcador.
- **Do** escribir etiquetas, controles y rótulos de gráfico en JetBrains Mono en mayúsculas con 0,06em (0,04em dentro de SVG).
- **Do** fijar en px el tamaño de las tarjetas de brújula y su lienzo SVG, y la altura del título.
- **Do** acompañar cada color de desvío con su cifra, tooltip o leyenda en texto.
- **Do** dibujar el Consensus en gris discontinuo (4/3) y la receta en tinta continua en todos los gráficos.
- **Do** redefinir los tokens en `[data-theme="dark"]` y en `prefers-color-scheme: dark` sin `[data-theme="light"]`, manteniendo el selector Claro / Oscuro / Auto.
- **Do** respetar `prefers-reduced-motion`: sin zoom animado del mapa ni escalado de entrada.

### Don't:
- **Don't** añadir sombras de elevación a ningún panel, tarjeta o control; la profundidad es filete y contraste de superficie.
- **Don't** usar #000000 como color de diseño; la tinta es #141414.
- **Don't** rellenar botones con color: el único botón relleno es el de tinta.
- **Don't** usar el amarillo como fondo de paneles o tarjetas; marca palabras, la celda elegida o la burbuja activa.
- **Don't** usar brasa ni verde como decoración: brasa es fuera de estrategia, verde es meta (la única excepción es el punto brasa del logotipo).
- **Don't** introducir una cuarta familia tipográfica ni pesos de display por encima de 600.
- **Don't** dimensionar las tarjetas de una rejilla 2 × 2 por su contenido.
