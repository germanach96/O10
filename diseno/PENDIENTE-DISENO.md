# Pendiente para el diseño nuevo

Decisiones tomadas al revisar el motor que la página todavía no refleja. Se añade una línea por decisión.

## Recetas
- **Eje nuevo `e` = años de estacionalidad (1 o 2).** La Brújula 1 sigue igual (X = peso estacional `s`, media plana ↔ estacionalidad), pero cada receta elige además si la parte estacional es el mismo mes del año anterior (1 año) o la media del mismo mes de los 2 años anteriores (2 años). Mostrarlo como un interruptor de la Brújula 1, no como un eje. Con `s = 0` no influye. En los códigos sin 2 años de historia, 2 años = 1 año.
- La rejilla gruesa pasa de 12.393 a **24.786 recetas** por código y foto. El texto "Coarse grid: … recipes" de la página calcula el total con una fórmula fija (`s.length**5 · N · celdas`) y tiene que incluir `e`.

## Datos
- **Códigos que salen del export** ("fantasmas"): cuentan en los trends de sus grupos, pero no salen en el mapa, el detector ni el nº de códigos del selector. La foto lleva un aviso nuevo ("N codes no longer in the export…"). Si algún día se muestran, su motivo de fuera de scope es "Fuera del export" (añadirlo a `TX`).
- **Trend de sell-out:** solo usa los meses en que el grupo tiene EPOS ese mes y hace 12 meses (el mes −1 sin EPOS cargado queda fuera). Si se explica en un tooltip, decirlo así.
