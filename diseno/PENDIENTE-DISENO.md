# Pendiente para el diseño nuevo

Traspaso para la conversación que haga el diseño. En una sesión dedicada solo al motor (sin tocar `interfaz/`) cambiamos el cálculo. La página todavía no lo refleja: `O10.0.1.html` y `diseno/ejemplos/BRUJULAS_ejemplo.html` se generaron con el motor anterior. Aquí está todo lo que cambió y lo que la página tiene que mostrar. La especificación (`CLAUDE.md`, secciones 1, 4 y 5) ya está actualizada.

## Antes de empezar: cuidado con el diseño (pedido expreso del usuario)

El usuario quiere que el diseño se haga **con mucho cuidado** y **siempre con las herramientas**. No apliques nada de memoria:

- **Carga las skills en la tarea actual** con la herramienta Skill: `impeccable:impeccable`, una de Taste (`design-taste-frontend`, `high-end-visual-design` o `redesign-existing-projects` si es rediseño), `emil-design-eng`, y **`apple-design`** (la página es estilo iOS / iPadOS 26 con cristal líquido; muelles, gestos, materiales y tipografía tienen que sentirse de Apple). Para animaciones, además `animate`.
- **Sigue `diseno/SKILLS-DISENO.md`** entero: tabla de comprobación al empezar, `impeccable detect --json` y tratar cada aviso, revisión final con `impeccable:impeccable-finish-reviewer` y documentación con `impeccable:impeccable-documenter`.
- **Comprueba con Playwright** (`mcp__playwright__…`): capturas en escritorio y móvil, en claro y oscuro, consola sin errores y tiempo de cada clic o filtro.
- **Figma** necesita que el usuario inicie sesión. Si hay un enlace, se lee antes de escribir código.
- Manda lo que pidió el usuario, después `diseno/PRODUCT.md` y `diseno/DESIGN.md`, y después Impeccable. Ningún paso de una skill se omite en silencio.

## Recetas: ejes nuevos

La receta pasa de 7 a 9 valores: `s, h, e, w, m, N, c, p, g` (este es el orden del índice plano).

- **`e` = años de estacionalidad (1 o 2).** 1 = mismo mes del año anterior; 2 = media del mismo mes de los 2 años anteriores. En los códigos sin 2 años de historia, 2 = 1.
  - **Mostrarlo como un interruptor de la Brújula 1, no como un eje.** La Brújula 1 sigue igual: X = peso estacional `s` (media plana ↔ estacionalidad), Y = peso del trend `w`.
- **`h` = de quién copio la estacionalidad**: Propio · Product Line · Brand · House.
  - Es **independiente del grupo del trend**. El selector de 17 celdas sigue siendo "de quién copio el trend"; hay que añadir dónde se ve y se elige el grupo de estacionalidad (por ejemplo, una fila de 4 opciones junto al selector o dentro de la Brújula 1). Las cuatro tarjetas de Decisiones tienen que seguir exactamente del mismo tamaño.
  - Tamaño de cada opción, para mostrarlo como en el selector: Propio = 1; Product Line, Brand y House = `tam_grupos` de las celdas "Product Line · Jerarquía", "Brand · Jerarquía" y "House · Jerarquía".
- Con `s = 0`, `e` y `h` no influyen: la página no debería destacarlos.
- **Rejilla: 99.144 recetas** por código y foto (antes 12.393): 3⁵ × 3 × 2 × 4 × 17. El texto "Coarse grid: … recipes" de la página calcula el total con una fórmula fija (`D.ejes.s.length**5 * D.ejes.N.length * CELDAS.length`) y tiene que incluir `e` y `h`.
- **Tope del trend: ±50%** (antes ±30%). Si algún texto o tooltip dice ±30%, cambiarlo; la página ya lo lee de `CFG.tope_trend`.
- **DAs:** se respetan siempre al 100%. No hay control para ignorarlos.

### Datos nuevos en `datos.json`

- `ejes` trae también `e` (`[1, 2]`) y `h` (`["Propio", "Product Line", "Brand", "House"]`, texto: traducir con `TX`).
- Cada receta (`txt`, `oraculo_receta`, `receta_txt`) trae las claves `e` y `h`.
- Los "mejores por eje" (`ejes` de cada código y de cada regla) traen también `e` y `h`: el mejor error alcanzable en cada valor. Sirven para posicionar el interruptor y las 4 opciones igual que los ejes de las brújulas.

## Datos y cálculo (cambios que la página puede tener que explicar)

- **Códigos que salen del export** ("fantasmas"): cuentan en los trends y en la estacionalidad de sus grupos con su historia y 0 desde que salieron. No salen en el mapa, el detector ni el nº de códigos del selector. La foto lleva un aviso nuevo ("N codes no longer in the export…"). Si algún día se muestran, su motivo de fuera de scope es "Fuera del export" (añadirlo a `TX`).
- **Actuals de códigos que salen del export:** se toman de la última foto que los trae y valen 0 después. Siguen midiéndose y sumando en sus grupos.
- **Trend de sell-out:** solo usa los meses en que el grupo tiene EPOS ese mes y hace 12 meses (el mes −1 sin EPOS cargado queda fuera). Antes salía sesgado a la baja (casa: −43% frente a −7% real). Si se explica en un tooltip, decirlo así.

## Qué cambió en los resultados (para textos, ejemplos y capturas)

- WAPE del oráculo en la casa: WAPE90 de 48.8% a 40.3% y WAPE 9M de 52.0% a 46.3% con la estacionalidad de grupo (antes de subir el tope a ±50%, que mejora unos 2–3 pp más).
- La media plana deja de dominar: la eligen ~15% de los oráculos (antes 57%). Los colores, ejemplos y textos que daban por hecho "casi todo plano" ya no valen.
- El pipeline tarda ~15 min para Gucci (antes ~2) y usa hasta ~7 GB de memoria. La página sigue sin calcular nada.

## Al terminar

- Regenerar la página con `python -m motor.pipeline` (tarda) y, si el usuario la aprueba, subir la versión según la sección 9 de `CLAUDE.md`.
