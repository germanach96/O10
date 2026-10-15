---
name: O10
description: App iOS / iPadOS 26 de cristal líquido para Demand Planning. Mapa de burbujas que flota sobre un fondo gris difuminado, inspector de cristal y brújulas de la mejor receta de forecast por código y foto.
colors:
  wallpaper: "#e9ebee"
  wallpaper-dark: "#0e0e0e"
  blob-light: "#ffffff"
  blob-shadow: "#c6cad1"
  blob-light-dark: "#2f2f2f"
  blob-shadow-dark: "#151515"
  glass: "rgba(255,255,255,.46)"
  glass-strong: "rgba(255,255,255,.72)"
  glass-edge: "rgba(255,255,255,.66)"
  glass-sheen: "rgba(255,255,255,.9)"
  glass-dark: "rgba(40,40,40,.46)"
  glass-strong-dark: "rgba(46,46,46,.78)"
  glass-edge-dark: "rgba(255,255,255,.13)"
  card: "#ffffff"
  card-dark: "#2c2c2e"
  fill: "rgba(120,120,128,.14)"
  fill-strong: "rgba(120,120,128,.24)"
  separator: "rgba(60,60,67,.14)"
  separator-strong: "rgba(60,60,67,.26)"
  label: "#1c1c1e"
  label-secondary: "#5d5d63"
  label-tertiary: "#6e6e74"
  label-dark: "#f5f5f7"
  label-secondary-dark: "#b2b2b8"
  system-blue: "#0071e3"
  system-blue-text: "#0062c4"
  system-blue-dark: "#0a72e8"
  system-blue-text-dark: "#74b8ff"
  on-blue: "#ffffff"
  consensus-gray: "#8e8e93"
  recipe-band: "rgba(0,113,227,.12)"
  goal-green: "#34c759"
  goal-green-text: "#1f7a35"
  goal-zone: "rgba(52,199,89,.16)"
  alert-red-text: "#c9001a"
  desvio-inside: "#9fa1a8"
  desvio-1: "#ffcc00"
  desvio-2: "#ff9500"
  desvio-3: "#ff3b30"
  desvio-4: "#b3001b"
  desvio-rim-0: "#6c6e75"
  desvio-rim-1: "#a37f00"
  desvio-rim-2: "#b86a00"
  desvio-rim-3: "#c4170c"
  desvio-rim-4: "#7a0012"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "36px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.028em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  card-title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "14.5px"
    fontWeight: 700
    lineHeight: "22px"
    letterSpacing: "-0.01em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "-0.003em"
  metric:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    letterSpacing: "-0.01em"
    fontFeature: "tnum"
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "11.5px"
    fontWeight: 500
    lineHeight: 1.3
  code:
    fontFamily: "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 400
    letterSpacing: "0"
rounded:
  s: "10px"
  row: "12px"
  m: "14px"
  l: "22px"
  xl: "28px"
  capsule: "999px"
spacing:
  hairline: "3px"
  xs: "6px"
  sm: "10px"
  float: "12px"
  md: "16px"
  grid: "20px"
  lg: "24px"
  section: "40px"
components:
  button-primary:
    backgroundColor: "{colors.system-blue}"
    textColor: "{colors.on-blue}"
    rounded: "{rounded.capsule}"
    padding: "8px 16px"
  button-tinted:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.label}"
    rounded: "{rounded.capsule}"
    padding: "8px 16px"
  button-round:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.capsule}"
    size: "42px"
  segmented-thumb:
    backgroundColor: "{colors.glass-strong}"
    textColor: "{colors.label}"
    rounded: "{rounded.capsule}"
    padding: "6px 16px"
  search-capsule:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.capsule}"
    height: "42px"
    width: "250px"
    padding: "0 14px"
  chip:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.label}"
    rounded: "{rounded.capsule}"
    padding: "4px 11px"
  chip-selected:
    backgroundColor: "{colors.system-blue}"
    textColor: "{colors.on-blue}"
    rounded: "{rounded.capsule}"
    padding: "4px 11px"
  sidebar:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.xl}"
    width: "264px"
    padding: "14px 10px 10px"
  sidebar-row-active:
    textColor: "{colors.system-blue-text}"
    rounded: "{rounded.row}"
    padding: "6px 10px"
  inspector:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.xl}"
    width: "332px"
    padding: "18px 16px 0"
  glass-card:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.l}"
    width: "360px"
    height: "548px"
    padding: "16px"
  results-card:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.l}"
    width: "260px"
    height: "374px"
    padding: "16px"
  detail-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.label}"
    rounded: "{rounded.l}"
    width: "260px"
    padding: "12px 14px"
  filters-popover:
    backgroundColor: "{colors.glass-strong}"
    textColor: "{colors.label}"
    rounded: "{rounded.l}"
    width: "450px"
    padding: "16px 18px"
  tab-bar:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.label}"
    rounded: "{rounded.capsule}"
    padding: "5px"
---

# Design System: O10

## Overview

**Creative North Star: "El cristal sobre la mesa gris"**

O10 es una app de iPadOS 26 que vive en una sola ventana sin marco: el contenido (el mapa de burbujas, las tarjetas de brújulas, las tablas) ocupa todo el lienzo, y todo lo que se manipula flota encima como piezas de cristal líquido. Debajo hay un papel tapiz quieto: un gris casi neutro con cuatro manchas suaves, difuminadas 48px y con un grano de ruido al 3,5%. Ese fondo no se mueve nunca; lo que se mueve son las burbujas, que derivan despacio y frenan en cuanto el puntero entra en el mapa, para poder leer y apuntar.

El color se reserva para los datos y la acción: azul de sistema para la receta y los botones, gris para el Consensus, verde para la meta y una escala ordinal amarillo, naranja, rojo para el desvío. Las superficies de cristal son incoloras: toman el tono de lo que tienen detrás. La densidad es de herramienta de trabajo (cuerpo de 13px, filas de 32px), con títulos grandes de iPadOS arriba de cada vista.

El movimiento sigue la física de Apple: muelles críticamente amortiguados, sin rebote, respuestas cortas al pulsar y nada que tarde en dejar leer un número. Con movimiento reducido no hay deriva, ni zoom animado, ni escalas.

**Key Characteristics:**
- Contenido a sangre sobre un fondo gris difuminado y estático; claro `#e9ebee`, oscuro en grises puros `#0e0e0e`.
- Un único material de cristal para todo lo flotante: barra lateral, cápsulas, inspector, popover, tarjetas de detalle y barra de pestañas.
- Burbujas hoja como lentes de cristal: tinte translúcido del tramo de desvío, aro del mismo tramo y reflejo especular arriba; sin sombreado de esfera.
- Colores de sistema de Apple con significado fijo; fuente del sistema.
- Deriva de 2,6px controlada por un solo bucle de animación con muelle sobre la amplitud.
- Apariencia manual Claro / Oscuro / Auto.

## Colors

Grises neutros de sistema para el fondo y el cristal; los colores saturados solo significan algo (acción, receta, meta, desvío).

### Primary
- **Azul de sistema** (system-blue / system-blue-dark): receta elegida en todas las gráficas, botón principal, chip seleccionado, fila activa de la barra lateral (al 16% de mezcla), anillo de foco al 55% y recuadro de la celda elegida del selector. En oscuro se usa un azul algo más profundo para que el texto blanco encima mantenga contraste.
- **Azul de texto** (system-blue-text / system-blue-text-dark): enlaces, migas, EANs enlazados, filas activas. Es la versión legible del azul sobre cristal; nunca uses el azul de relleno para texto pequeño.
- **Banda de la receta** (recipe-band): rango de tolerancia alrededor de la receta en la gráfica de la foto actual.

### Secondary
- **Gris Consensus** (consensus-gray): lo que pasó. Trayectoria discontinua en las medias brújulas y línea del Consensus frente a la receta.
- **Verde meta** (goal-green, goal-green-text, goal-zone): zona WAPE ≤ 40% y SPP ±5% en las medias brújulas y valores que cumplen la meta (`.bueno`). El rojo de texto (alert-red-text) marca los que no la cumplen y los desvíos de la tabla del detector.

### Tertiary: escala ordinal de desvío
- **Dentro** (desvio-inside), **Hasta 5%** (desvio-1, amarillo), **5–15%** (desvio-2, naranja), **15–30%** (desvio-3, rojo), **Más de 30%** (desvio-4, granate). Rellenan las burbujas hoja con opacidad 0,62 (0,74 y 0,9 en los dos tramos altos, 0,6 en oscuro) y cada tramo tiene su aro más oscuro (desvio-rim-0 … desvio-rim-4; en oscuro los aros son más claros). El modo oscuro aclara la escala (`#ffd60a`, `#ff9f0a`, `#ff6a3d`, `#ff375f`) en lugar de oscurecerla.

### Neutral
- **Papel tapiz** (wallpaper / wallpaper-dark) con sus manchas (blob-*): el único fondo de la app.
- **Cristal** (glass, glass-strong y sus versiones oscuras): relleno translúcido de todas las piezas flotantes; el fuerte se usa en el popover, el pulgar del segmentado y las etiquetas de grupo del mapa.
- **Borde y brillo de cristal** (glass-edge, glass-sheen): el filo de 1px y el reflejo interior superior.
- **Tarjeta sólida** (card / card-dark): fondo de la tarjeta de detalle (al 88%), de la barra lateral y la barra de pestañas en iPhone, y de todo el cristal cuando se pide menos transparencia.
- **Rellenos** (fill, fill-strong): pozos de controles, chips, celdas de KPI, filas al pasar.
- **Separadores** (separator, separator-strong) y **etiquetas** (label, label-secondary, label-tertiary): jerarquía de texto de iOS.

### Named Rules
**La Regla del Cristal Incoloro.** El cristal no lleva tinte de marca: es blanco o gris translúcido y toma el color del fondo. El color va en los datos, nunca en el material.

**La Regla del Significado Fijo.** Azul = receta y acción; gris = Consensus; verde = meta; amarillo → rojo = desvío. Ningún color cambia de papel entre vistas, y el color nunca es la única señal: la tarjeta de detalle y la leyenda nombran el tramo.

**La Regla de los Grises Puros.** El modo oscuro es gris neutro (`#0e0e0e` de fondo, manchas `#151515`–`#393939`), sin tinte azulado.

## Typography

**Display Font:** fuente del sistema (SF Pro Display, con Helvetica Neue, Segoe UI, Roboto y Arial de reserva)
**Body Font:** fuente del sistema (SF Pro Text, con la misma pila)
**Label/Mono Font:** ui-monospace / SF Mono, solo para EANs y códigos

**Character:** La voz de iPadOS sin disfraz: títulos grandes y apretados en 700 con interletraje negativo, cuerpo compacto de herramienta, cifras siempre tabulares.

### Hierarchy
- **Display** (700, 36px, 1.1, −0.028em): título del código o grupo en la vista Detalle, hasta 26ch, con balanceo de líneas.
- **Headline** (700, 30px, 1.1, −0.025em): título grande de la barra superior (nombre de la casa o del nivel del mapa). 28px en iPhone.
- **Title** (700, 24px, 1.15–1.2, −0.025em): títulos de sección del Detalle y título del inspector.
- **Card title** (700, 14.5px, altura fija de 22px): título de cada tarjeta de brújula, en una línea con elipsis; el subtítulo tiene altura fija de 36px para que las cuatro tarjetas alineen.
- **Body** (400, 13px, 1.45): texto general, filas, resúmenes.
- **Metric** (700, 16px, tabular): cifras de KPI en las fichas; 14px en la tarjeta de detalle.
- **Label** (500–600, 11–12px): cabeceras de lista, leyendas, rótulos de los grupos de filtros, encabezados de la barra lateral (11px 600, en minúscula de frase).
- **Code** (400, 11.5px, monoespaciada): EANs.

### Named Rules
**La Regla de las Cifras Tabulares.** Todo número (KPI, desvío, unidades, recuentos, ejes) usa cifras tabulares para que las columnas no bailen.

**La Regla de la Minúscula de Frase.** Los rótulos van en minúscula de frase, como en iOS. Nada de rótulos en mayúsculas espaciadas encima de los títulos.

## Layout

Ventana a sangre, sin lienzo enmarcado. En iPad / escritorio (más de 900px):

- **Barra lateral** flotante de 264px, separada 12px de los bordes, de arriba abajo.
- **Contenido** desde 288px a la derecha. Arriba, una barra con el título grande a la izquierda y las cápsulas a la derecha (segmentado Mapa / Detalle, botón redondo de filtros, cápsula de búsqueda de 250px), con 10px entre cápsulas. Al hacer scroll aparece detrás un velo difuminado con máscara degradada.
- **Mapa**: lienzo circular cuadrado de `min(100%, 100dvh − 150px)` centrado, con la leyenda en cápsula de cristal debajo; a su derecha, el **inspector** de 332px que flota desde 84px arriba hasta 12px abajo.
- **Detalle**: columna con secciones separadas 40px; rejillas de tarjetas de 2 × 360px con 20px de hueco (una columna por debajo de 820px). A partir de 1360px aparece un raíl de resumen de 280px pegajoso a la derecha.

En iPhone (900px o menos) todo pasa a una columna con scroll de página: barra superior pegajosa con la búsqueda a todo el ancho, mapa a todo el ancho, **barra de pestañas** de cristal flotante abajo (Mapa, Detalle, Brands, Filtros), el inspector como hoja inferior y la barra lateral y los filtros como hojas que suben desde abajo. Se respetan las zonas seguras (`env(safe-area-inset-*)`).

El ritmo usa pasos de 3, 6, 10, 12, 16, 20, 24 y 40px; 12px es la distancia de flotación de toda pieza de cristal al borde.

## Elevation & Depth

La profundidad es material, no tonal: el fondo está abajo, el contenido a sangre encima, y el cristal flota por encima de todo. Cada pieza de cristal combina relleno translúcido, `backdrop-filter: blur(28px) saturate(185%)` (40px en el popover, 36px en la tarjeta de detalle, 44px en las hojas de iPhone), un filo de 1px, una línea de brillo interior arriba, un reflejo especular diagonal en `soft-light` y una sombra suave y amplia.

### Shadow Vocabulary
- **Sombra de cristal clara** (`box-shadow: 0 10px 34px rgba(30,36,48,.12), 0 1px 3px rgba(30,36,48,.08)`): toda pieza flotante.
- **Sombra de cristal oscura** (`box-shadow: 0 12px 40px rgba(0,0,0,.5), 0 1px 3px rgba(0,0,0,.4)`): la misma en modo oscuro.
- **Brillo interior** (`inset 0 1px 0 <glass-sheen>, inset 0 -1px 1px rgba(255,255,255,.08)`): filo superior luminoso y luz de rebote abajo.
- **Halo del botón principal** (`0 4px 14px color-mix(in srgb, <azul> 35%, transparent), inset 0 1px 0 rgba(255,255,255,.3)`): el único elemento con sombra de color.
- **Pulgar del segmentado** (`0 2px 8px rgba(0,0,0,.12), inset 0 1px 0 <glass-sheen>, 0 0 0 .5px <glass-edge>`).

### Named Rules
**La Regla del Fondo Quieto.** El papel tapiz no se anima nunca. Solo se mueve el contenido, y solo cuando el puntero no está encima.

**La Regla de la Lente, no la Esfera.** Las burbujas son lentes planas de cristal: reflejo especular arriba, luz de borde abajo, tinte translúcido. Sin gradiente radial de volumen ni sombra proyectada.

**La Regla del Cristal Accesible.** Con `prefers-reduced-transparency` todo el cristal pasa a tarjeta sólida y el fondo deja de difuminarse; con `prefers-contrast: more` el borde del cristal se oscurece y el cristal se vuelve casi opaco.

## Shapes

Esquinas continuas de iOS en cuatro tamaños: 10px para campos pequeños y foco, 12px para filas y celdas, 14px para grupos del raíl, 22px para tarjetas, popover y tarjeta de detalle, 28px para las piezas grandes (barra lateral, inspector y hojas de iPhone, solo con las esquinas superiores redondeadas). Todo control es cápsula (999px): botones, segmentados, chips, búsqueda, barra de pestañas, etiquetas de grupo del mapa. El mapa es un círculo recortado; las burbujas son círculos anidados (casa, brand, product line, EAN) con filo de 1px que no escala con el zoom.

## Components

### Buttons
- **Shape:** cápsula (999px).
- **Primary:** azul de sistema con texto blanco, 13px 600, 8px × 16px, con halo azul suave y brillo interior.
- **Tinted:** relleno gris de sistema, texto de etiqueta, sin sombra.
- **Round:** botón de cristal de 42px (filtros, menú en iPhone) con contador azul de 17px en la esquina cuando hay filtros activos.
- **Link:** texto azul sin fondo, subrayado solo al pasar con puntero fino.
- **Press:** escala 0,96 (0,93 en los redondos, 0,94–0,98 en pestañas y filas) en 140ms con ease-out fuerte; los estados hover solo existen con `(hover: hover) and (pointer: fine)`.

### Segmented control
- Cápsula con pulgar de cristal que se desliza bajo la opción elegida (`transform` y `width` en 360ms con la curva de muelle `linear()`). Se usa para Mapa / Detalle y para Claro / Oscuro / Auto.

### Chips
- **Style:** cápsula de relleno gris, 12px 500, 4px × 11px.
- **State:** seleccionado = azul con texto blanco (`aria-pressed`); hover = relleno más fuerte.

### Cards / Containers
- **Corner Style:** 22px (tarjetas), 28px (barra lateral e inspector).
- **Background:** cristal; la ficha interna del inspector usa cristal blanco al 55% con filo de cristal.
- **Shadow Strategy:** sombra de cristal (ver Elevation & Depth).
- **Border:** filo de cristal de 1px.
- **Internal Padding:** 16px en tarjetas; 14px en fichas; celdas de KPI de 8 × 9px con radio de 12px.
- **Decisiones:** las cuatro tarjetas (Brújula 1, 2, 3 y selector) miden exactamente 360 × 548px, con lienzo SVG fijo de 326px.
- **Resultados:** tres tarjetas de 260 × 374px (`.tarjeta.res`) en una rejilla `repeat(auto-fill, 260px)` con 20px de separación (una columna en iPhone), con lienzo SVG de 228 × 196px.

### Decisiones (brújulas y selector)
- **Tira de años de estacionalidad** (`svg#b1e`, `.tira-e`, 326 × 62px) bajo el lienzo de la Brújula 1: rótulo "Years of seasonality · e" a la izquierda y la elección a la derecha (azul si hay receta, gris si no aplica). Un punto por foto, de 1 año (abajo) a 2 años (arriba), con la misma regla de posición que las brújulas; la línea discontinua del centro es la zona indiferente. Con s = 0 la tira recibe la clase `.inerte` y baja al 42% de opacidad.
- **Selector** ("Selector · Whose trend and seasonality?"): filas del trend de 50px (Hierarchy, + Segmento, + Tamaño, + Edad) y, bajo un separador, una fila "Seasonality" de 46px alineada con las columnas Own · Line · Brand · House. Misma escala de tamaño (relleno azul con opacidad logarítmica según el nº de códigos); la celda elegida lleva aro de 2px en azul receta. Con s = 0 la fila de estacionalidad queda al 40% de opacidad.

### Resultados (medias brújulas)
- Tres medias brújulas (SPP3·WAPE90, SPP6·WAPE180, SPP·WAPE 9M) con **escala común adaptativa**: SPP ±30/50/75/100/150/200/300% y WAPE 60/80/100/150/200/300/400%, el primer escalón que cubre todos los valores con un 6% de margen.
- Encima, una fila de leyenda (`.ley-graf`, 12px, etiqueta secundaria); debajo de cada gráfico, la tabla de KPIs `.t-kpi` (12px; cabeceras 11px 600; primera columna en etiqueta secundaria). Sin tarjeta "Cómo leerlas".

### Detector
- **Bloque de fórmula** (`.formula`): relleno gris (`fill`), radio 14px (`--r-m`), relleno interior 14px × 16px. Título 14px 700; la fórmula (`.fx`) en 15px con los valores de la receta en azul de texto 700 y los operadores en etiqueta secundaria; definiciones (`.def`) en 12,5px. Debajo, chips de parámetros (`.pars`): cápsulas con fondo de tarjeta, 12px, valor en azul de texto 600; los que no influyen (s = 0) van tachados en la fórmula y al 50% en los chips (`.nulo`).
- **Tabla:** columna "Recipe" (`.c-rec`, mínimo 230px) en dos líneas: el grupo en etiqueta y los valores debajo en 11px y etiqueta secundaria.

### Inputs / Fields
- **Search capsule:** cristal de 42px de alto, icono de lupa, placeholder en etiqueta secundaria; 16px de texto en iPhone para que Safari no haga zoom.
- **Campos pequeños** (tolerancias, selects): pozo de relleno gris, radio 9–10px, cifras alineadas a la derecha.
- **Focus:** contorno azul al 55% de 3px con 2px de separación; la búsqueda añade un halo azul de 4px al 35%.

### Navigation
- **Barra lateral:** cabecera con el icono de la app y "O10", selector de casa, encabezados de sección en 11px 600, filas de 32px con icono azul y contador en cápsula; fila activa con fondo azul al 16% y texto azul. Abajo, el segmentado de apariencia. Los triángulos de despliegue giran 90° en 220ms.
- **iPhone:** barra de pestañas de cristal flotante centrada abajo; pestaña activa con relleno gris y texto azul. La barra lateral sube como hoja (420ms, curva de cajón `cubic-bezier(0.32,0.72,0,1)`) con velo del 22%.

### Mapa de burbujas (signature)
- Burbujas anidadas: casa transparente, brands y product lines con cristal blanco tenue y filo claro, hojas EAN como lentes de cristal tintadas por tramo de desvío. Códigos sin receta: aro discontinuo; códigos local: hueco con filo gris.
- **Deriva:** cada burbuja se desplaza como mucho 2,6px en pantalla (a cualquier zoom, y nunca fuera de su grupo) con periodos propios de 9–16s. Un solo bucle `requestAnimationFrame` mueve todas; un muelle críticamente amortiguado (respuesta ≈ 0,7s) lleva la amplitud a 0 al entrar el puntero y a 1 al salir. El bucle se detiene con la pestaña oculta y no arranca con movimiento reducido.
- **Hover:** la hoja señalada crece a 1,07 en 200ms ease-out con filo blanco de 2,5px.
- **Zoom:** al entrar en un grupo, transformación en 640ms con la curva de muelle `linear()`; las etiquetas se desvanecen con un desenfoque de 4px.
- **Etiquetas de grupo:** cápsulas de cristal fuerte de 11,5px 600 con el recuento en etiqueta secundaria.

### Tarjeta de detalle
- Cristal casi opaco (tarjeta al 88%, blur 36px) de 260px anclada a la burbuja. La primera aparece en 150ms (opacidad, desenfoque de 4px y escala de 0,96 a 1); mientras sigue visible, las siguientes cambian al instante, como los tooltips de Apple. Muestra EAN, descripción, KPIs en celdas de relleno y una nota.

### Popover de filtros
- Cristal fuerte de 450px que nace del botón que lo abre (`transform-origin` en el botón): entra en 240ms ease-out desde escala 0,94, −6px y desenfoque de 6px; sale en 140ms. En iPhone es una hoja inferior.

### Inspector (hoja en iPhone)
- En iPad, panel de cristal fijo a la derecha. En iPhone, hoja inferior con dos posiciones (asomada 270px / abierta), agarradera de 38 × 5px; se arrastra 1:1 y al soltar elige la posición proyectando la velocidad; transición de 420ms con la curva de cajón.

## Do's and Don'ts

### Do:
- **Do** usar un único material de cristal (relleno translúcido, blur 28px saturate 185%, filo de 1px, brillo superior, sombra suave) para todo lo que flota.
- **Do** dejar que el contenido llegue a los bordes y separar las piezas flotantes 12px del borde.
- **Do** mantener el papel tapiz gris, difuminado y quieto en los dos modos.
- **Do** usar azul solo para receta y acción, gris para Consensus, verde para la meta y la escala amarillo → rojo para el desvío.
- **Do** usar cifras tabulares en todo número y la fuente del sistema en todo texto.
- **Do** animar con muelles críticamente amortiguados y curvas ease-out fuertes, respetar `prefers-reduced-motion` y `prefers-reduced-transparency`, y reservar el hover para punteros finos.
- **Do** mantener todas las tarjetas de cada rejilla del mismo tamaño fijo (360 × 548px en Decisiones, 260 × 374px en Resultados).

### Don't:
- **Don't** animar el fondo ni añadir fondos en movimiento.
- **Don't** dar volumen de esfera a las burbujas (gradiente radial, sombra proyectada): son lentes planas.
- **Don't** teñir el cristal con color de marca ni usar azul para decorar.
- **Don't** usar grises azulados en el modo oscuro.
- **Don't** poner rótulos en mayúsculas espaciadas sobre los títulos.
- **Don't** usar animaciones con rebote ni que retrasen la lectura de un número más de 640ms.
