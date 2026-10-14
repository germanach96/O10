---
name: Brújulas de Demand
description: App de Mac para Demand Planning. Mapa de burbujas, inspector y brújulas de la mejor receta de forecast por código y foto.
colors:
  window-bg: "#f5f5f7"
  surface: "#ffffff"
  surface-secondary: "#f5f5f7"
  sidebar: "#ececef"
  control-fill: "rgba(118,118,128,.12)"
  control-fill-strong: "rgba(118,118,128,.20)"
  separator: "rgba(60,60,67,.16)"
  separator-strong: "rgba(60,60,67,.29)"
  label: "#1d1d1f"
  label-secondary: "#6e6e73"
  label-tertiary: "#76767b"
  system-blue: "#0071e3"
  system-blue-text: "#0066cc"
  on-blue: "#ffffff"
  consensus-gray: "#8e8e93"
  recipe-band: "rgba(0,113,227,.10)"
  goal-green: "#34c759"
  goal-green-text: "#248a3d"
  goal-zone: "rgba(52,199,89,.14)"
  warning-orange: "#ff9500"
  alert-red: "#ff3b30"
  alert-red-text: "#d70015"
  desvio-inside: "#d1d1d6"
  desvio-1: "#ffcc00"
  desvio-2: "#ff9500"
  desvio-3: "#ff3b30"
  desvio-4: "#b3001b"
  bubble-empty: "#aeaeb2"
  bubble-norecipe: "#e5e5ea"
  bubble-pl: "#f2f2f5"
  toolbar-material: "rgba(245,245,247,.72)"
  dark-window-bg: "#1c1c1e"
  dark-surface: "#2c2c2e"
  dark-surface-secondary: "#3a3a3c"
  dark-sidebar: "#252527"
  dark-label: "#f5f5f7"
  dark-label-secondary: "#aeaeb2"
  dark-system-blue: "#0a72e8"
  dark-system-blue-text: "#4ea1ff"
  dark-goal-green: "#30d158"
  dark-alert-red-text: "#ff6961"
  dark-desvio-3: "#ff6a3d"
  dark-desvio-4: "#ff375f"
typography:
  large-title:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  metric-hero:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.03em"
    fontFeature: "\"tnum\""
  title-1:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.022em"
  metric:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    letterSpacing: "-0.01em"
    fontFeature: "\"tnum\""
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title-3:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: "22px"
    letterSpacing: "-0.01em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "-0.003em"
  callout:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "12.5px"
    fontWeight: 500
    fontFeature: "\"tnum\""
  caption:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "11.5px"
    fontWeight: 400
    lineHeight: 1.45
  section-header:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"Helvetica Neue\", \"Segoe UI\", Roboto, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "0.01em"
  code:
    fontFamily: "ui-monospace, \"SF Mono\", SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 400
    letterSpacing: "0"
rounded:
  s: "6px"
  control: "8px"
  m: "10px"
  l: "16px"
  canvas: "22px"
  pill: "999px"
spacing:
  xxs: "2px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  section: "40px"
components:
  button-primary:
    backgroundColor: "{colors.system-blue}"
    textColor: "{colors.on-blue}"
    typography: "{typography.body}"
    rounded: "{rounded.s}"
    padding: "5px 12px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.label}"
    rounded: "{rounded.s}"
    padding: "5px 12px"
  button-icon:
    backgroundColor: "transparent"
    textColor: "{colors.label-secondary}"
    rounded: "{rounded.s}"
    width: "30px"
    height: "28px"
  button-icon-hover:
    backgroundColor: "{colors.control-fill}"
    textColor: "{colors.label}"
  segmented-control:
    backgroundColor: "{colors.control-fill}"
    textColor: "{colors.label}"
    rounded: "{rounded.control}"
    padding: "2px"
  segmented-thumb:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.s}"
  search-field:
    backgroundColor: "{colors.control-fill}"
    textColor: "{colors.label}"
    rounded: "7px"
    height: "28px"
    width: "240px"
  search-field-focus:
    backgroundColor: "{colors.surface}"
  chip:
    backgroundColor: "{colors.control-fill}"
    textColor: "{colors.label}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
  chip-selected:
    backgroundColor: "{colors.system-blue}"
    textColor: "{colors.on-blue}"
  sidebar-row:
    backgroundColor: "transparent"
    textColor: "{colors.label}"
    rounded: "{rounded.s}"
    padding: "5px 8px"
    height: "28px"
  sidebar-row-selected:
    backgroundColor: "{colors.system-blue}"
    textColor: "{colors.on-blue}"
  badge:
    backgroundColor: "{colors.control-fill}"
    textColor: "{colors.label-secondary}"
    rounded: "{rounded.pill}"
    padding: "1px 7px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.l}"
    padding: "16px"
  compass-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.l}"
    padding: "16px"
    width: "360px"
    height: "480px"
  inspector-sheet:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.m}"
    padding: "14px"
  toolbar:
    backgroundColor: "{colors.toolbar-material}"
    padding: "8px 16px"
    height: "52px"
---

# Design System: Brújulas de Demand

## Overview

**Creative North Star: "La app de Mac recién salida de Cupertino"**

Brújulas de Demand se ve y se comporta como una app nativa de macOS nueva. No imita el estilo de Apple como decoración: usa sus convenciones de ventana. Barra lateral con lista de fuentes y vistas inteligentes, barra de herramientas translúcida, contenido central sobre superficies agrupadas y una columna de inspector a la derecha. Todo lo que el planner conoce de Finder, Notas o Música le sirve aquí sin aprender nada.

La densidad es la de una herramienta de trabajo. El cuerpo es de 13px, como en macOS. Las filas de la barra lateral miden 28px, los controles son compactos y los números van siempre en cifras tabulares. La jerarquía no la da el tamaño sino el peso y el color de la etiqueta (primaria, secundaria, terciaria). El único gesto grande es el título del detalle, que pasa a la barra cuando sale de la vista.

El color sigue los colores del sistema de Apple y cada uno tiene un solo trabajo. Azul para la receta y para la selección, gris para el Consensus, verde para la meta y una escala ordinal amarillo → naranja → rojo para el desvío. Hay modo claro, modo oscuro y Auto, que se eligen a mano en la barra lateral. El movimiento es un muelle críticamente amortiguado, sin rebote.

**Key Characteristics:**
- Ventana en tres columnas: barra lateral (260px), contenido y un inspector de 320px.
- Fuente del sistema (SF Pro vía `-apple-system`), cuerpo de 13px y cifras tabulares en todos los datos.
- Superficies agrupadas blancas sobre el gris de ventana, separadas por un filo de media línea y no por bordes gruesos.
- Material translúcido solo donde el contenido pasa por debajo (barra de herramientas, popover, tooltip, etiquetas de burbuja).
- Muelle críticamente amortiguado para el zoom del mapa y el pulgar de los segmentados; respeta movimiento y transparencia reducidos.

## Colors

Colores del sistema de Apple en claro y oscuro: neutros grises sin tinte y acentos saturados que solo aparecen cuando significan algo. Los pares oscuros figuran en el frontmatter con el prefijo `dark-`.

### Primary
- **Azul del sistema** (system-blue / dark-system-blue): fila seleccionada de la barra lateral y de la lista del inspector, botón principal, chip activo, recuadro del grupo elegido en el selector, anillo de foco y trayectoria de la mejor receta en las brújulas. En oscuro baja a un azul algo más profundo que el `#0a84ff` de Apple para que el texto blanco encima mantenga el contraste.
- **Azul de texto** (system-blue-text / dark-system-blue-text): enlaces, migas activas, EAN clicables y el texto "Elegido". Nunca se usa para rellenos.
- **Banda de receta** (recipe-band): la banda de tolerancia alrededor de la receta en el gráfico de la foto actual.

### Secondary
- **Gris Consensus** (consensus-gray): lo que pasó de verdad. Siempre con línea discontinua (4 3) para que se distinga del azul también sin color.

### Tertiary
- **Verde meta** (goal-green, goal-zone, goal-green-text): la zona WAPE ≤ 40% y SPP ±5% de las medias brújulas, su línea discontinua y los valores que cumplen la meta.
- **Escala de desvío** (desvio-inside, desvio-1 … desvio-4): gris = dentro, amarillo hasta 5%, naranja 5–15%, rojo 15–30% y granate por encima del 30%. Colorea las hojas del mapa y sus muestras en la leyenda. El texto sobre cada tono cambia (oscuro en los claros, blanco en el granate claro) para mantener AA.
- **Rojo de alerta** (alert-red-text): la cifra grande de desvío del inspector y la celda de desvío de las filas fuera de estrategia.
- **Naranja de aviso** (warning-orange): avisos en línea, como "historia corta".

### Neutral
- **Gris de ventana** (window-bg / dark-window-bg): lienzo de la ventana y fondo del inspector.
- **Superficie** (surface / dark-surface): tarjetas, fichas, el lienzo del mapa, el pulgar del segmentado en claro y los popups.
- **Superficie secundaria** (surface-secondary / dark-surface-secondary): bloques dentro de una tarjeta (la tira de KPIs, los grupos del rail).
- **Barra lateral** (sidebar / dark-sidebar): un gris un punto más oscuro que la ventana.
- **Rellenos de control** (control-fill, control-fill-strong): fondo del segmentado, del buscador, de los chips y de las filas al pasar el ratón.
- **Separadores** (separator, separator-strong): filos de media línea en tarjetas y líneas de tabla. La versión fuerte es para cabeceras de tabla y contornos de control.
- **Etiquetas** (label, label-secondary, label-tertiary): los tres niveles de texto. Casi toda la jerarquía se hace con ellos.
- **Burbujas** (bubble-pl, bubble-empty, bubble-norecipe): relleno de las product lines, contorno de los huecos y de los códigos sin receta (estos últimos con trazo punteado).

### Named Rules
**La regla de un color, un trabajo.** El azul es la receta y la selección, el gris es el Consensus, el verde es la meta, y la escala amarilla-roja es el desvío. Ningún color cambia de papel entre vistas.

**La regla del color acompañado.** El desvío nunca se comunica solo con color: cada tono va con su tramo en la leyenda, una cifra en la lista y un tooltip. El Consensus además de gris es discontinuo.

## Typography

**Display Font:** SF Pro Display (vía `-apple-system`, con Helvetica Neue, Segoe UI, Roboto y Arial de reserva)
**Body Font:** SF Pro Text (vía `-apple-system`, misma cadena)
**Label/Mono Font:** SF Mono (`ui-monospace`) solo para EAN y códigos

**Character:** una sola familia, la del sistema, como en cualquier app de Apple. La personalidad sale del tracking negativo en los tamaños grandes y del contraste entre negrita 700 y regular, no de una fuente con carácter.

### Hierarchy
- **Large title** (700, 34px, 1.1): nombre del código o grupo en el detalle. Cuando sale de la vista, el título pasa a la barra de herramientas.
- **Metric hero** (700, 40px, 1.05): la cifra de desvío del inspector del detalle.
- **Title 1** (700, 22px, 1.15): título del inspector y de cada sección del detalle.
- **Metric** (600, 17–20px, tabulares): KPIs de la ficha y del rail.
- **Headline** (600, 15px): título de la ventana en la barra de herramientas.
- **Title 3** (600, 14px, alto fijo de 22px): títulos de las tarjetas de brújula, con una sola línea y elipsis para que las cuatro tarjetas queden alineadas.
- **Body** (400, 13px, 1.45): texto base de la app, filas y tablas.
- **Callout** (500, 12.5px, tabulares): segmentados, tablas y valores de la lista.
- **Caption** (400, 11.5px): migas, leyendas, etiquetas de burbuja y notas.
- **Section header** (600, 11px, etiqueta secundaria, sin mayúsculas forzadas): encabezados de la barra lateral ("Códigos", "Brands"), de las columnas de lista y de los grupos del rail, como los encabezados de lista de fuentes de macOS.

### Named Rules
**La regla de las cifras tabulares.** Cualquier número (KPI, desvío, contador o eje) lleva `font-variant-numeric: tabular-nums`, para que las columnas no bailen al ordenar ni al cambiar de foto.

**La regla de la fuente del sistema.** No se carga ninguna fuente web. Si el SO no tiene SF Pro, la cadena cae a la fuente nativa de cada plataforma.

## Layout

Es una ventana de app, no una página. Ocupa `100dvh`, en una rejilla de dos columnas: la barra lateral de 260px y el contenido. El scroll vive dentro de cada vista, no en el body. El Mapa reparte el contenido en el lienzo de burbujas (cuadrado, con un ancho de `min(100%, 100dvh − 150px)`) y el inspector de 320px. El Detalle es una columna de lectura con márgenes de 28px y secciones separadas por 40px. A partir de 1360px suma un rail de resumen fijo de 280px a la derecha; por debajo, el rail sube antes de las secciones.

Las tarjetas de Decisiones y Resultados forman una rejilla de 2 × 2 de tamaño fijo: 360px de ancho, 480px de alto las brújulas y 410px las medias brújulas. El lienzo SVG mide 326px y el título tiene un alto fijo, así que las cuatro tarjetas siempre quedan iguales y alineadas.

El ritmo de espaciado es de 4 en 4 (2, 4, 8, 12, 16, 20, 40), con pasos impares heredados de macOS en los controles (5px y 7px de relleno vertical).

Por debajo de 900px la barra lateral se convierte en una hoja deslizante sobre un velo, el buscador baja a una fila propia (a 16px para que iOS no haga zoom), el inspector va debajo del mapa, la rejilla de tarjetas pasa a una columna y el detector se lee como lista de dos columnas. El popover de filtros pasa a ser una hoja inferior.

### Named Rules
**La regla del tamaño fijo.** Las tarjetas de brújula tienen ancho, alto y altura de título fijos en px. Ningún contenido las estira.

## Elevation & Depth

Es un sistema híbrido, como macOS. Las superficies en reposo se separan por tono (blanco sobre gris) y por un filo interior de media línea. Las sombras son suaves y ambientales, y crecen solo con lo que flota. Los materiales translúcidos (`saturate(180%) blur(20–30px)`) se reservan para lo que tiene contenido debajo: la barra de herramientas, el popover de filtros, el tooltip y las píldoras de etiqueta del mapa. La barra de herramientas no tiene borde en reposo; el separador aparece en cuanto el contenido pasa por debajo.

### Shadow Vocabulary
- **Reposo** (`box-shadow: 0 1px 2px rgba(0,0,0,.06), 0 1px 1px rgba(0,0,0,.04)`): tarjetas, fichas, botones y popups, siempre junto con el filo `inset 0 0 0 .5px` del separador.
- **Lienzo** (`box-shadow: 0 4px 14px rgba(0,0,0,.08), 0 1px 3px rgba(0,0,0,.06)`): el lienzo del mapa, la superficie principal.
- **Flotante** (`box-shadow: 0 12px 40px rgba(0,0,0,.16), 0 2px 8px rgba(0,0,0,.08)`): popover, tooltip y hoja lateral.
- En oscuro, las tres sombras suben de opacidad (de .4 a .55) porque el negro sobre gris oscuro se ve menos.

### Named Rules
**La regla del material con motivo.** El desenfoque translúcido solo existe donde hay contenido debajo. Con `prefers-reduced-transparency`, todos los materiales pasan a un fondo opaco.

## Shapes

Esquinas continuas y suaves al estilo Apple, con un radio según el tamaño de la pieza. 6px en controles y filas, 8px en el segmentado y en los bloques internos, 10px en fichas y tooltips, 16px en tarjetas y popovers y 22px en el lienzo del mapa. Los chips, los contadores y las etiquetas de grupo son píldoras. La forma propia del producto es el círculo: burbujas anidadas para casa, brand, product line y EAN, puntos de trayectoria (9px el último, 5px los antiguos, con un aro del color de la superficie) y las brújulas, que también son círculos. El icono de la app es un squircle azul con una brújula blanca. Los iconos de la interfaz son SVG de trazo de 1.6px, en una caja de 16px y con remates redondos.

## Components

### Buttons
Discretos y táctiles, como los botones de una hoja de macOS.
- **Shape:** esquinas suaves (6px).
- **Primary:** azul del sistema con texto blanco, peso 500, relleno 5px 12px y sombra de reposo. Uno por bloque como mucho ("Abrir brújulas del código", "Hecho").
- **Secondary:** superficie blanca con el filo de separador fuerte y texto en la etiqueta primaria ("Subir un nivel").
- **Icon:** 30 × 28px, transparente, con el icono en la etiqueta secundaria. Al pasar el ratón toma el relleno de control; abierto (`aria-expanded`) toma el relleno fuerte. Puede llevar un contador azul en la esquina.
- **Press:** `scale(.97)` y `brightness(.92)` en 120ms ease-out. Los hovers solo se activan con `hover: hover` y puntero fino.
- **Link:** texto en azul de texto sin fondo, subrayado al pasar el ratón con un offset de 3px.

### Segmented Control
- Pista con el relleno de control (radio de 8px, 2px de relleno) y un pulgar blanco (gris `#636366` en oscuro) que se desliza con el muelle en 320ms. Se usa para Mapa/Detalle en la barra y para Claro/Oscuro/Auto en el pie de la barra lateral.

### Chips
- **Style:** píldora con el relleno de control, 12px y relleno 3px 10px.
- **State:** activo en azul del sistema con texto blanco (`aria-pressed`). Al pulsar, `scale(.96)`. Viven en el popover de filtros, en filas con la etiqueta alineada a 92px.

### Cards / Containers
- **Corner Style:** 16px en tarjetas y bloques anchos, 10px en las fichas del inspector y 22px en el lienzo.
- **Background:** superficie sobre el gris de ventana. Los bloques internos van en superficie secundaria con un radio de 8–10px.
- **Shadow Strategy:** sombra de reposo con el filo de media línea (ver Elevation & Depth).
- **Border:** ninguno; solo el filo `inset 0 0 0 .5px`.
- **Internal Padding:** 14–18px.

### Inputs / Fields
- **Search:** campo redondeado de 28px con el relleno de control, una lupa SVG y la pista `⌘K`, que abre la búsqueda de verdad. Al enfocar pasa a la superficie con un halo azul de 3px.
- **Popup / select:** superficie con el filo fuerte, la sombra de reposo y el chevron doble de macOS dibujado en SVG.
- **Number:** alineado a la derecha, con cifras tabulares y el filo de separador fuerte.
- **Focus:** anillo azul de 3px al 55% con un offset de 1px en todo elemento enfocado con teclado.

### Navigation
- **Barra lateral:** cabecera con el icono de la app; un popup de casa; las secciones "Códigos" (vistas inteligentes con iconos azules y contadores en píldora) y "Brands" (con flechas de despliegue que giran 90° y sublistas sangradas 18px); y el selector de apariencia en el pie. La fila seleccionada se rellena de azul con el texto, el icono y el contador en blanco.
- **Barra de herramientas:** de 52px, translúcida y sticky, con el título de 15px y las migas debajo; luego el segmentado de vista, el botón de filtros y el buscador. En el Detalle el título de la barra solo aparece cuando el título grande sale de la vista.
- **Móvil:** la barra lateral pasa a hoja deslizante (380ms, curva de cajón) y un botón de icono la abre.

### Mapa de burbujas (signature)
Círculos anidados casa → brand → product line → EAN dentro de un lienzo cuadrado de 22px de radio. Las brands son blancas con el filo fuerte, las product lines van en el gris de product line y las hojas llevan el color de su tramo de desvío con un aro de la superficie. Lo filtrado se apaga al 16%. El zoom al grupo es una transformación con el muelle de 620ms. Las etiquetas de grupo son píldoras translúcidas y se desvanecen con un desenfoque de 3px mientras el mapa se mueve.

### Brújulas y medias brújulas (signature)
Círculos dibujados en SVG de 326px, con cada polo en su extremo y texto de 10.5px en la etiqueta secundaria. La trayectoria de la receta va en azul: un punto por foto, los antiguos más tenues, el último más grande y el mes rotulado en el primero y en el último. En las medias brújulas el Consensus va en gris discontinuo, y la zona meta es verde con la línea discontinua de WAPE 40%.

### Selector de grupo
Una matriz de 17 celdas de 40px de alto con un radio de 7px. La intensidad del azul crece con el logaritmo del tamaño del grupo y el texto pasa de negro a blanco según el contraste real de cada celda. La celda elegida lleva un doble anillo (2px de superficie y 4px de azul).

### Inspector
Una columna de 320px sobre el gris de ventana, con el título 1, un resumen en la etiqueta secundaria, acciones, una ficha con la tira de tres KPIs y una lista de códigos que se desvanece con una máscara en los últimos 24px. La fila activa de la lista se rellena de azul.

## Do's and Don'ts

### Do:
- **Do** usar los tokens de color del sistema en las dos apariencias; cada token claro tiene su par oscuro y se cambian juntos con `data-theme` o `prefers-color-scheme`.
- **Do** separar las superficies por tono y por el filo `inset 0 0 0 .5px` del separador, y guardar las sombras grandes para lo que flota.
- **Do** animar con el muelle críticamente amortiguado (`--muelle`, 320–620ms) para lo que se mueve en el espacio y con `cubic-bezier(0.23,1,0.32,1)` en 120–220ms para la respuesta al pulsar y los popovers.
- **Do** desactivar transformaciones y desenfoques con `prefers-reduced-motion`, y quitar materiales con `prefers-reduced-transparency`.
- **Do** dibujar el Consensus en gris discontinuo y la receta en azul continuo en todos los gráficos.
- **Do** dibujar los iconos como SVG de trazo de 1.6px en una caja de 16px.

### Don't:
- **Don't** cargar fuentes web ni usar una fuente de display distinta de la del sistema.
- **Don't** usar el azul para algo que no sea la receta, la selección, el foco o un enlace.
- **Don't** usar la escala amarilla-roja fuera del desvío, ni dejar el desvío sin su cifra o su tooltip.
- **Don't** poner desenfoque translúcido en superficies que no tienen contenido debajo.
- **Don't** dejar que una tarjeta de brújula cambie de tamaño con su contenido.
- **Don't** poner bordes de 1px opacos alrededor de las tarjetas; el filo es de media línea y semitransparente.
