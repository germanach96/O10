# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Demand planners** de Coty (Barcelona Supply Chain Hub), cada uno con sus casas. Entran para encontrar rápido un código, una brand o una product line, ver si su Consensus se sale de la receta elegida y bajar a sus brújulas.
- **Managers de Demand Planning**, que miran la casa entera: qué brands y product lines acumulan más desvío frente a la estrategia, sin llegar necesariamente al código.

## Product Purpose
Brújulas de Demand responde, foto a foto, a "¿qué inputs de forecast debí haber puesto en esa foto para tener los mejores KPIs?". Con todas las fotos elige una sola receta por código y detecta los códigos cuyo Consensus actual se sale de esa receta. Éxito: el planner llega en segundos al código o grupo que tiene que revisar y entiende por qué.

## Positioning
No es un forecast nuevo: es un oráculo retrospectivo sobre los propios datos del equipo (Actuals, EPOS, Supply Cuts, Total Demand Assumption) que traduce 12.393 recetas por código y foto a tres brújulas y un selector de grupo, más un detector frente a la receta elegida.

## Operating Context
- Un CSV por casa y foto mensual (export S&OP). Todo se precalcula con `python -m motor.pipeline`; la página es un HTML autocontenido que solo lee y se abre sin servidor.
- Jerarquía: House → Brand → Product Line → EAN. Scope central: Regular Item con responsable Central o vacío; los códigos local cuentan en los agregados.
- Interfaz y comentarios en español.

## Capabilities and Constraints
- KPIs en unidades: WAPE90/SPP3, WAPE180/SPP6, WAPE/SPP 9M. Metas: WAPE ≤ 40%, SPP ±5%. SPP negativo = sobre-forecast.
- Detector: desvío por mes = solo el exceso fuera de la tolerancia (por defecto 5%, opción gradual), sumado en valor absoluto; columnas en unidades y en %.
- Las especificaciones completas viven en `CLAUDE.md`.

## Evidence on Hand
- Datos reales de Gucci: `data/Gucci/Consensus/Gucci_2025_11.csv` y `Gucci_2026_09.csv` (524 EANs, 10 brands, 58 product lines en la foto 2026.M09).
- No hay logos, fotografías ni testimonios: no inventarlos.

## Product Principles
1. Llegar al código o grupo que importa en segundos: filtrar primero, leer después.
2. Los números mandan: cada visual se puede leer en unidades y en % y se apoya en datos del cubo, nunca en adornos.
3. Mismo lenguaje que los reportes del equipo (signos, nombres de KPIs, tramos).
4. Precalculado y sin dependencias: la página nunca recalcula el motor.

## Accessibility & Inclusion
Modo claro y oscuro con selector manual. Contraste AA en textos y controles; el color nunca es la única señal (tooltip y texto acompañan al color del desvío).
