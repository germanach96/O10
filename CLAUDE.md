# Brújulas de Demand — especificación para Claude Code

Herramienta para el equipo de Demand Planning (Coty, Barcelona Supply Chain Hub).
Responde, foto a foto, a una pregunta: **"¿qué inputs de forecast debí haber puesto en esa foto para tener los mejores KPIs?"**.
Después, con todas las fotos, elige **una sola receta por código** para el forecast futuro y detecta los códigos cuyo Consensus actual se sale de esa receta.

Fase 1 (esta especificación): encontrar, en cada foto, los parámetros que minimizan el WAPE, para todas las fotos y todos los códigos del scope, guardarlos y mostrarlos. La búsqueda de tendencias y patrones entre fotos se define más adelante.

Idioma de la interfaz y de los comentarios: español.

Mapa del repo: `README.md`. Cálculo en `motor/`, página en `interfaz/`, decisiones de diseño y HTML de ejemplo en `diseno/`, CSV en `data/<Casa>/Consensus/` (y `data/<Casa>/Promos/`, aún sin usar).

Reglas de diseño (skills obligatorias Impeccable, Emil Kowalski, Taste, Figma y Playwright): @diseno/SKILLS-DISENO.md

---

## 1. KPIs

Los 6 KPIs del equipo. Todos en **unidades**, divididos entre **actuals**.

| KPI | Foto usada (mes de medición M) | Ventana medida | Ejemplo, medición en octubre |
|---|---|---|---|
| SPP3 / WAPE90 | M−4 | M−3 … M−1 | foto de junio, jul–sep |
| SPP6 / WAPE180 | M−7 | M−6 … M−1 | foto de marzo, abr–sep |
| SPP / WAPE (short term, 9M) | M−10 | M−9 … M−1 | foto de diciembre del año anterior, ene–sep |

Visto desde una foto F: forecast de los meses F+1 … F+9. SPP3/WAPE90 = meses F+1…F+3, SPP6/WAPE180 = F+1…F+6, SPP/WAPE = F+1…F+9.

- **WAPE** = Σ|Forecast − Actual| / Σ Actual. La suma de errores absolutos: no compensa meses ni códigos.
- **SPP** = Σ(Forecast − Actual) / Σ Actual, con signo, es el bias. **SPP negativo = sobre-forecast** (convención del equipo; respetar el signo que use el equipo en sus reportes, y si hay duda, preguntar).
- En un grupo se suman numeradores y denominadores de todos los códigos y meses. Ejemplo: línea con dos códigos a −5% y +5% → WAPE 10%, SPP 0%.
- **Metas:** WAPE ≤ 40% (todos los WAPE) y SPP entre −5% y +5% (todos los SPP).

**Actuals de un mes M:** se toman de cualquier foto posterior a M (la más reciente disponible). Nunca de la foto del propio mes M.

---

## 2. Datos de entrada

Un CSV por **casa** y **foto mensual** (ejemplo: `Gucci_2026_04.csv` = casa Gucci, foto S&OP 2026.M04). Se guardan en `data/<Casa>/Consensus/` (por ejemplo `data/Gucci/Consensus/Gucci_2026_04.csv`). Hay una carpeta por casa (Gucci, Gucci MU, Kylie MU, Kylie Frag, Burberry, Burberry MU, Marc Jacobs MU), cada una con `Consensus/` y `Promos/`; `Promos/` aún no se lee.

### Formato
- Separador `;`, codificación UTF-8 con BOM.
- **Dos filas de cabecera.** La 1ª solo trae `S&OP AAAA.MXX` encima de las columnas de medidas (de ahí, o del nombre del archivo, sale el mes de la foto). La 2ª trae los nombres de columna.
- Formato largo: una fila por código × mes. Meses naturales `AAAA.MXX` (rango típico 2021.M01–2030.M12).
- Hay **filas vacías al final** (solo `;`): descartarlas.
- **Celda vacía ≠ 0.** Hay ceros explícitos; distinguir "sin dato" de "cero".
- Puede haber decimales con punto en el Consensus.
- **EAN:** en el export de prueba salió en notación científica (`3.61423E+12`), lo que lo hace inútil como clave. El usuario va a reexportar con el EAN como texto. Leer siempre el EAN como texto y **validar** al cargar: si un EAN tiene notación científica o hay menos EANs distintos que descripciones, abortar con un mensaje claro.
- Año fiscal: empieza en julio (2026.M01 = FY26.Q3). Se mezclan meses naturales con Q/FY fiscales; está bien así.

### Columnas y uso

| Columna | Uso |
|---|---|
| Sub-Division, House, Brand, Product Line | Jerarquía: House → Brand → Product Line → código |
| Article Type | `Regular Item` / `One Shot/Promo` (scope) |
| EAN | Clave del código (texto) |
| Planning Item Description | Descripción; de aquí se extrae el **tamaño** |
| Core Category, Sub-Category, Market Category | Atributos (informativos) |
| Fiscal Year, Fiscal Quarter, Month | Tiempo |
| Final Responsibility | `Central` / `Local` / vacío (scope) |
| Ignore System Forecast Flag | 1 = uno de los CFGs (normalmente el de más volumen) no deja fluir el System FC al Consensus. 2 = todo manual, el sistema no fluye. Vacío = el sistema fluye |
| System FC - Final | Forecast estadístico |
| Initiative Forecast, Prometheus Fcst Consensus | Capas del forecast (informativas) |
| **EPOS** | **Sell-out.** Solo para calcular trends. **Nunca en valor absoluto** (no todos los retailers reportan) |
| Reasonability Adjustment | Columna donde se aplicarán los ajustes que proponga la tool. Hoy vacía |
| **Total Demand Assumption** | **Promos / DAs.** Tomar el valor tal cual, positivo o negativo (la diferenciación por tipo vendrá en una 2ª etapa) |
| **Consensus - Final** | Forecast comprometido. Es el que se mide en los KPIs y el que vigila el detector |
| **Actuals** | **Sell-in** |
| **Supply Cuts** | Cortes de inventario (generan órdenes repetidas) |
| Final Segment | Rabbits, Horses, Bulls, Post NPI, DISC. Vacío se queda vacío |
| Disco Date | Fecha de discontinuación `dd/mm/aaaa`. `23/12/2030` = valor por defecto (sin fecha real) |

### Reglas de tiempo
- **En los meses pasados el forecast está sobrescrito por los actuals** (demand control: System FC y Consensus = Actuals). El forecast de un mes solo se puede sacar de una foto anterior a ese mes.
- **El mes en curso de cada foto se ignora siempre** (actuals parciales, demasiados movimientos). En la foto 2026.M04, la historia útil llega hasta 2026.M03 y el forecast evaluado empieza en 2026.M05.
- Nada posterior a la foto puede entrar en el cálculo de una receta de esa foto (sin look-ahead).

### Atributos derivados
- **Tamaño:** extraer de la descripción (`50 ML`, `90ML`, `150 ML`, `10ml`, `3.5 G`…). Normalizar a número + unidad.
- **Edad:** desde el primer mes con actuals > 0. Tramos:
  - Año 1, meses 1–6 (innovación local, fuera de scope)
  - Año 1, meses 7–12
  - Año 2
  - Año 3+
  - **Pre-disco:** los 12 meses antes de una Disco Date real. **Tiene prioridad** sobre los otros tramos.
  - Si el código ya vendía en el primer mes de la historia (2021.M01), su edad real es desconocida: tratarlo como año 3+.

---

## 3. Scope

- **Se calculan (central):**
  - Regular Item con Final Responsibility `Central` o vacía.
  - Incluidos los que tienen Ignore System Forecast Flag 1 o 2 (sirve para evaluar si conviene quitar el flag).
  - Códigos de iniciativa en sus meses 7–12 del año 1.
- **No se calculan para nada (local):**
  - One Shot/Promo, aunque el responsable esté vacío.
  - Innovaciones en sus meses 1–6.
- **Pero los volúmenes de los códigos local sí cuentan** en los trends de grupo y en los cálculos agregados (puede haber canibalismo o efecto halo).
- **Filtro general de tipos** (barra lateral de inicio, "Cuentan en los cálculos"): Regular / One Shot (Article Type) y Central (o vacío) / Local (Final Responsibility). Por defecto cuentan todos. Un tipo apagado no suma en los trends de grupo ni en el tamaño de los grupos, y desaparece del mapa y del detector. Al menos un tipo de cada pareja queda encendido. Se precalcula cada combinación de One Shot y Local (`filtro_tipos` en la configuración); apagar Regular o Central deja el scope vacío y no necesita cálculo. El cubo, los logs y los resúmenes en disco son los de la variante base (no se ignora nada).

- **Dos clases de filtro, que no se mezclan:**
  - **Filtros de cálculo** = el filtro de tipos de arriba ("Cuentan en los cálculos"): lo que se apaga queda fuera de TODO (scope, trends, tamaño de grupos, mapa y detector).
  - **Filtros de selección** = el popover de filtros (scope, segmento, edad, fuera de estrategia, búsqueda): solo eligen QUÉ códigos se miran. Por defecto el scope es **Todos** (One Shot e innovaciones se ven y se pueden elegir); "Central" es un filtro más. Con un filtro activo, "Ver brújulas" de un grupo abre el detalle de los códigos filtrados de ese grupo (por ejemplo, los Bulls de Gucci Flora), como una selección del modo acumulado: los trends y los cálculos se hacen con todos los códigos y cada código conserva su receta; los resultados, el detector y el esquema muestran solo los filtrados. En el modo acumulado, agregar un grupo con filtro agrega el grupo filtrado.
  - **Listas** (filtros de selección propios): `data/filters.csv`, una lista por columna (cabecera = nombre, debajo sus EANs como texto; separador `;`). En el popover van en una sección **Listas** plegable al final (recuerda si estaba abierta), con una fila por lista: marca, nombre y cuántos de sus EANs hay en la casa y cuentan en los cálculos ("26 de 120"). Varias listas elegidas se suman (una u otra) y se cruzan con el resto de filtros. Los EANs que no están en la casa se ignoran. Una lista sin ningún código en la casa queda apagada ("Ninguno en Gucci"); si sus códigos existen pero el filtro de cálculo los saca (por ejemplo, solo One Shots con One Shot apagado), queda "Fuera de los cálculos" y, si está elegida, no selecciona nada. El filtro guardado en la clave de la selección incluye el scope: sin "Central" entran todos los códigos filtrados, también One Shot e innovaciones.

El scope se evalúa en cada foto: un código puede entrar en la foto de octubre porque ya cumplió 7 meses.

---

## 4. Recetas: las variables de decisión

Una **receta** es una combinación de valores de estas variables. Horizonte: short term, 9 meses.

### Brújula 1 — "¿Cuánto me alejo de la media?"
- **X · Peso estacional `s`**: 0% = media plana ↔ 100% = mismo mes del año pasado.
- **Y · Peso del trend `w`**: 0% = sin trend (solo la base) ↔ 100% = trend completo.
- **Tope del trend:** parámetro fijo, por defecto ±30%. No es un eje.

### Brújula 2 — "¿Qué señal sigo?"
- **X · Mezcla `m`**: 100% sell-in (Actuals) ↔ 100% sell-out (EPOS). 50% = promedio de los dos trends.
- **Y · Duración `N`** del trend: 6M, 9M o 12M.

### Brújula 3 — "¿Cómo limpio la historia?" (actuals excepcionales)
- **X · Cortes `c`**: cuánto de los Supply Cuts se suma a la historia (0% … 100%).
- **Y · Promos `p`**: cuánto de la Total Demand Assumption se resta de la historia (0% … 100%).

### Selector — "¿De quién copio el trend?" (una sola opción, tipo botón)
- Matriz **amplitud × criterio**:
  - Columnas, amplitud: Propio (el código), Product Line, Brand, House, Todo.
  - Filas, criterio adicional: Solo jerarquía, + Segmento, + Tamaño, + Edad.
  - "Propio" solo existe en la fila "Solo jerarquía" → 17 celdas.
- El grupo se forma con los códigos que comparten la amplitud y el criterio con el código evaluado (ejemplo: Brand + Edad = misma brand y mismo tramo de edad). Incluye códigos local.
- **El valor que muestra cada celda es el nº de códigos del grupo**, para ver qué tan grande es el grupo que seguimos.

### Rejilla
- **Gruesa (la que se calcula y guarda completa):**
  - `s, w, m, c, p` ∈ {0, 50, 100}%
  - `N` ∈ {6, 9, 12}
  - 17 grupos
  - Total: 3⁵ × 3 × 17 = **12.393 recetas** por código y foto.
- **Fina (opcional):** pasos de 25% alrededor del ganador de la gruesa, calculada al vuelo. Pasos más finos no tienen sentido de negocio.
- Las rejillas y el tope deben estar en un archivo de configuración, no en el código.

---

## 5. Cómo se construye el forecast de una receta

Para un código, una foto F y una receta (s, w, m, N, c, p, grupo G). Historia disponible: meses ≤ F−1.

1. **Historia limpia (sell-in):** H(t) = Actuals(t) + c · SupplyCuts(t) − p · TDA(t), con celdas vacías = 0 en cortes y TDA.
2. **Base para el mes futuro t:** Base(t) = (1 − s) · Media(H) + s · H(t − 12).
   - Media(H) = media de H de los últimos 12 meses cerrados. **Decisión abierta:** confirmar con el usuario si la media debe ser de 12M u otra.
   - H(t − 12) = mismo mes del año anterior. Para t > F + 12 no aplica (el horizonte es de 9 meses).
3. **Trend del grupo G con duración N:**
   - T_sellin = Σ H_G(últimos N meses) / Σ H_G(mismos N meses del año anterior) − 1, donde H_G es la historia limpia sumada de todos los códigos del grupo.
   - T_sellout = igual con EPOS, sin limpiar, solo meses en que el grupo tiene EPOS.
   - T = (1 − m) · T_sellin + m · T_sellout, recortado a ±tope.
4. **Forecast:** F(t) = Base(t) · (1 + w · T) + **DAs futuros**(t), donde DAs futuros = Total Demand Assumption de la foto F para el mes t (lo planificado se suma encima de la base).
5. Forecast negativo → 0.

### Casos límite (registrar, no romper)
- Código sin 12 meses de historia: no hay año anterior. Las recetas con `s > 0` usan la media; marcar el código como "historia corta".
- Grupo sin historia del año anterior o con denominador 0: trend no calculable; esa receta queda inválida para ese código.
- Grupo sin EPOS: las recetas con `m > 0` quedan inválidas.
- Llevar un log por foto con los códigos y recetas inválidos y el motivo.

---

## 6. Medición y elección

### Por foto (nivel oráculo)
Para cada código del scope, cada receta y cada **tramo** de meses (1–3, 4–6, 7–9 desde la foto):
- `abs_err` = Σ|F − A|
- `sgn_err` = Σ(F − A)
- `act` = Σ A
- `cons_abs`, `cons_sgn` = lo mismo para el Consensus - Final real de la foto, para comparar con lo que se hizo.

Un tramo está **cerrado** cuando todos sus meses tienen actuals (en alguna foto posterior) y no son el mes en curso. Los tramos abiertos no se usan.

**Mejor receta de un código en una foto:** la de menor WAPE en la ventana evaluada. **El SPP solo sirve como desempate** (menor |SPP|).

Dos niveles de resultado:
- **Oráculo:** mejor receta por código y foto. Es lo que se dibuja como trayectoria; sirve para entender, no se aplica directamente.
- **Regla:** mejor receta por grupo a lo largo de varias fotos (score de la sección siguiente, sumando todos los códigos del grupo).

### Elegir UNA receta para el futuro (con todas las fotos)
El corto plazo pesa más (a 6–9 meses faltan insights de mercado). Pesos por tramo **wₕ = 4 (meses 1–3), 2 (4–6), 1 (7–9)**. Equivale a WAPE90 ×2 + WAPE180 + WAPE9M, porque las ventanas están anidadas.

```
Score(receta) = Σ_fotos dₓ · Σ_tramos cerrados wₕ · abs_err
              / Σ_fotos dₓ · Σ_tramos cerrados wₕ · act
```
- dₓ = 1 para todas las fotos por ahora. La fórmula debe permitir cambiarlo, por ejemplo dₓ = 0,5^(meses de antigüedad / 6) para dar más peso a lo reciente. Parámetro en configuración.
- Cada foto aporta solo sus tramos cerrados.
- Gana el menor score. Desempate: menor |SPP| con la misma ponderación.

---

## 7. Detector de desvíos frente a la estrategia

Compara el **Consensus - Final de la foto más actual** con el forecast de la **receta elegida** para cada código, mes a mes, en los 9 meses futuros.

- **Tolerancia** definida por el usuario. Por defecto 5% en todo el horizonte. **Primero se fija una tolerancia general en la pantalla de inicio** (barra lateral, "Ajustes generales") y después, en el detalle de un EAN, se le puede poner una **tolerancia propia** que sustituye a la general solo para ese EAN (se marca con ● en el detector). En un grupo, cada código usa la suya. Se guarda en el navegador del usuario. Opción gradual lineal:
  `tol(h) = inicio + (fin − inicio) · (h − 1) / 8`, h = 1…9. Ejemplo: 5% → 10% da 7,5% en el mes 5.
- **Desvío de un mes:** solo el exceso fuera del rango. Tolerancia 5% y Consensus 8% por encima de la receta → desvío 3%. Dentro del rango → 0.
- **Resultado por EAN, como el WAPE:** suma en **valor absoluto** de los desvíos de todos los meses. No es bias: un mes por encima y otro por debajo no se compensan.
- Dos columnas, ambas ordenables:
  - **Desvío en unidades** (impacto).
  - **Desvío en %** = desvío en unidades / Σ forecast de la receta en el horizonte.
- Salida: lista de EANs fuera de su estrategia, con los meses que se salen.

---

## 8. Arquitectura de cálculo

- **Precalcular una vez por foto y guardar; la página solo lee.** No recalcular al navegar.
- Python + numpy/pandas vectorizado. La rejilla gruesa completa para ~200 códigos se calcula en segundos.
- **Almacenamiento del cubo:** Parquet, una partición por casa y foto, consultable con DuckDB.
  - Filas: foto × código × receta × tramo, con `abs_err`, `sgn_err` y `act`.
  - Guardar **numeradores, no porcentajes**: así el WAPE y el SPP de cualquier grupo o ponderación salen sumando y dividiendo.
- **Resumen por foto para la página** (JSON pequeño):
  - mejor receta por código y sus KPIs por ventana;
  - KPIs del Consensus real;
  - para cada eje de cada brújula, el mejor error alcanzable en cada valor del eje;
  - nº de códigos y WAPE de cada celda del selector;
  - mejor receta por grupo.
- **Al llegar una foto nueva:**
  1. Cargar y validar la foto.
  2. Calcular las recetas de esa foto (tramos aún abiertos).
  3. Con los actuals nuevos, **cerrar tramos de fotos antiguas** y completar sus errores. Ejemplo: la foto de abril cierra SPP3 en agosto, SPP6 en noviembre y el de 9M en febrero.
  4. Regenerar los resúmenes afectados.
- La receta y el forecast de cada receta quedan fijados en el momento de su foto; solo cambian los actuals que se le comparan.

---

## 9. Interfaz

El programa se llama **O10**. Estilo **iOS / iPadOS 26 (cristal líquido)**; el sistema completo está en `diseno/DESIGN.md` (la guía `diseno/referencia/DESIGN html.md` queda como referencia antigua, ya no se aplica). Modo claro, oscuro y automático con selector.

### Decisiones de diseño (fijadas por el usuario)
- **Estructura tipo iPad, todo flotando:** el mapa ocupa toda la ventana y encima flotan piezas de cristal: barra lateral (casa, vistas inteligentes con contador, brands desplegables hasta product line, apariencia), cápsulas de control arriba (Mapa / Detalle, filtros en popover, buscador con ⌘K) e inspector a la derecha.
- **iPhone:** barra de pestañas flotante (Mapa, Detalle, Brands, Filtros), inspector como hoja inferior arrastrable con dos posiciones y brands como hoja.
- **Página de inicio = burbujas anidadas** (todas las casas) → casa → brand → product line → EAN. **La casa es un círculo más** (cristal, con su etiqueta): en el futuro convivirán varias casas en el mapa; la raíz "Todas las casas" es invisible y, con una sola casa cargada, el mapa empieza enfocado en ella (no un grafo de fuerza, demasiado sucio con ~500 códigos). Tamaño = Consensus - Final de la foto más actual en los 6 meses cerrados anteriores (en pasado el Consensus ya es igual a los actuals: lo vendido) más los 12 meses siguientes (lo que se planea vender); el mes en curso no entra. Color = desvío del Consensus frente a la receta elegida, escala ordinal **verde (dentro del rango**, el verde de meta, algo más claro y translúcido para separarse de los rojos también por luminosidad) → amarillo → naranja → rojo → rojo oscuro; los códigos que no cumplen los filtros quedan en gris tenue; fuera de scope con color propio y relleno translúcido: **One Shot = marrón** (`--c-os`, systemBrown) e **innovaciones en sus meses 1-6 = cian** (`--c-in`, systemCyan; un One Shot nuevo cuenta como One Shot); el resto de fuera de scope, huecos.
- **Burbujas como lentes de cristal** (tinte translúcido, borde de luz, reflejo superior). Flotan muy despacio (≈2–3 px, ciclos de 9–16 s); al entrar el puntero en el mapa **todas frenan** con un muelle sin rebote y la burbuja señalada crece y muestra una tarjeta de cristal con su detalle. Con movimiento reducido no flotan.
- **Sin recorte al hacer zoom:** las burbujas nunca se cortan con un círculo ni con el borde del lienzo; siempre están visibles y, si pasan por debajo de la barra, la barra lateral o el inspector, se ven a través del cristal (desenfoque tipo iOS 26).
- **Cámara libre en el mapa:** arrastrar con el botón pulsado (o el dedo) mueve el mapa 1:1 y al soltar sigue con inercia (deceleración 0,998/ms, como el scroll de iOS); en los bordes resiste con goma y vuelve con un muelle sin rebote. La rueda (o el pellizco) hace zoom alrededor del puntero. Un clic sigue entrando un nivel (casa → brand → product line → EAN); si el nivel ya se ve entero y grande, la cámara no se mueve. Las etiquetas se ocultan mientras la cámara se mueve y se recolocan al parar, para todo lo que se vea a ese zoom. Botón **"Ver todo"** arriba a la derecha del mapa: vuelve al encuadre completo con el muelle de la cámara (atenuado si ya se ve todo).
- **Al reordenarse el mapa** (filtro de tipos, tolerancia, rango): la vista no vuelve al encuadre del foco. Se ancla al grupo que se está mirando (el más profundo que contiene el centro de la vista) y la cámara se recoloca para que siga en el mismo sitio y tamaño en pantalla. **Coreografía en tres tiempos:** 1) las que dejan de contar se desvanecen donde estaban (180 ms, encogiendo a 0,9); 2) las que siguen esperan quietas y van todas juntas a su sitio nuevo (FLIP en coordenadas de pantalla desde lo que se ve, muelle de 560 ms; los círculos de grupo se vuelven translúcidos mientras viajan para no tapar lo que cruzan); 3) cuando el movimiento ya casi se asentó (≈70 %) entran las nuevas con fundido y escala 0,92 → 1 (260 ms). Si solo se quitan, no hay paso 3; si solo se ponen, no hay paso 1. Se animan todas las visibles (ninguna llega antes que su grupo) y las etiquetas reaparecen al terminar. Un segundo clic a medio camino retoma desde lo que se ve, sin saltos. Con movimiento reducido, solo un fundido. El botón del filtro responde al instante y el recálculo va en el fotograma siguiente.
- **Indicador de nivel** en la barra de arriba, junto a Mapa / Detalle (solo en la vista del mapa; en iPhone, en su propia fila): cápsula segmentada Todas · Casa · Brand · Línea · EAN con el nivel actual marcado (el pulgar se desliza con el muelle de los controles; los niveles de arriba se pueden pulsar para subir, los de abajo están apagados). Sin texto de instrucciones. Al pasar el puntero, el aro azul y la tarjeta van en lo que el clic elegiría (el siguiente nivel desde el foco), no en la burbuja más pequeña bajo el puntero. Las etiquetas del mapa nunca quedan debajo de "Ver todo".
- **Barra lateral:** ajustes generales y la lista **Casas y brands** (casa → brands → product lines, desplegable como en Finder). Sin las vistas "Todos los códigos / En scope / Fuera de estrategia" (lo cubren los filtros).
- **Modo acumulado** (interruptor arriba del inspector): en cada nivel (casa, brand, product line o EAN) aparece "Agregar a la selección" y se forma una lista (bandeja con quitar y vaciar; se guarda en el navegador por casa). Los elementos de la lista llevan un anillo azul en el mapa. "Ver brújulas de la selección" abre el detalle de la selección.
- **Detalle de una selección:** se dibuja como un grupo (punto grande = promedio de los códigos, cada código pequeño), pero **no tiene receta común**: cada código conserva su propia receta y copia el trend de su propio grupo (un Gucci Flora y un Guilty usan trends de brands distintas). Los KPIs suman los numeradores de cada código (WAPE = Σ|F−A| / ΣA). El selector muestra el grupo de trend más copiado.
- **Fondo:** gris difuminado y quieto (en oscuro, grises puros). **Selección marcada:** el nivel actual y el EAN elegido llevan el mismo aro azul firme (sin halo); el aro de "lo que elegiría el clic" es más tenue.
- **Colores del sistema de Apple con un significado fijo:** azul = receta y acciones, gris discontinuo = Consensus, verde = meta. Fuente del sistema.
- **Movimiento** según la skill de Emil Kowalski: muelles críticamente amortiguados para zoom y controles, curvas ease-out fuertes para pulsaciones y popovers, nada animado en acciones de teclado.

Selector de casa y de código (desde el mapa, la barra lateral o el buscador).

### Barra de rango de cálculo (fija arriba, en el mapa y en el detalle)
- Un punto por cada foto cargada de la casa y dos tiradores para elegir la primera y la última foto. **Solo se pueden elegir fotos medidas**: las fotos aún sin tramos cerrados van al final, huecas, sobre un tramo discontinuo con la etiqueta "Sin medir aún", y los tiradores no pasan de la última foto medida (tope duro, sin goma). Las fotos dentro del rango van en azul con la etiqueta en negrita. Atajos: Todo, Últimas 6, Últimas 3 (las últimas fotos medidas).
- El relleno azul se coloca con `left`/`width` en px (no con `scaleX` de 1 px, que se descuadra con el zoom del navegador). Las etiquetas de mes se ocultan si no caben (≥ 34 px entre ellas). Por debajo de 1220 px la barra pasa a dos filas; en iPhone, al bajar, se compacta como en iOS (título pequeño, sin buscador ni atajos).
- Arrastre 1:1 con captura del puntero; el recálculo pesado se hace al soltar, fuera del fotograma del gesto; al soltar se proyecta la inercia y encaja en la foto más cercana con un muelle sin rebote. Con teclado: flechas, Inicio y Fin, sin animación.
- **Todo cambia con el rango:** solo las fotos medidas del rango eligen la receta de cada código y de cada grupo (y, con ella, el detector y el color de las burbujas); brújulas, mapa de calor, selector y resultados muestran solo esas fotos. El detector sigue comparando el Consensus de la foto más reciente.
- La página no calcula: el pipeline precalcula cada rango contiguo de fotos medidas (n·(n+1)/2; 55 con 10 fotos) guardando solo índices de receta, y el forecast de la foto actual una vez por (código, receta) usada. El rango se recuerda en el navegador.

### Detalle en 4 grupos
- **Cabecera:** migas, título y, junto al título, un botón **?** con los detalles (tipo de regla o atributos del código, fotos medidas y avisos de las fotos). No se muestran de base: aparecen al pasar el puntero y, al pulsar el ?, quedan fijos hasta volver a pulsarlo, Escape o un clic fuera.
- **Esquema de la selección** arriba de la columna de resumen (fija al hacer scroll): el mapa de burbujas completo en pequeño, con los códigos que entran en el reporte en azul (y un aro en el grupo o el código elegido) y "N de M códigos". Al pulsarlo vuelve al mapa enfocado en esa selección.
- El detalle se agrupa en **cuatro grupos, y solo cuatro**: Foto actual, Decisiones, Resultados y Detector. No se parten en subsectores.
- **Al abrir la página los cuatro empiezan plegados:** cada grupo deja su título y una tira de cristal con lo esencial (Foto actual: desvío, % sobre la receta, meses o códigos fuera; Decisiones: la receta elegida; Resultados: WAPE90 y WAPE 9M de la receta frente al Consensus y la mejora; Detector: EANs fuera, desvío total y el mayor). Al pulsar el título o la tira, el grupo se expande (la tira crece hasta ser el contenido, View Transition con curva de cajón de iOS) y su cabecera no se mueve en pantalla. Botón "Expandir todo" / "Plegar todo" junto al título. El índice lateral abre el grupo antes de ir a él.

### Sección "Decisiones" — rejilla 2 × 2
- Tres brújulas cuadradas (Brújula 1, 2 y 3) y, en el cuarto cuadro, el selector de grupo.
- **Las cuatro tarjetas exactamente del mismo tamaño y alineadas.** Los prototipos fallaron aquí: usar un tamaño fijo en px para el lienzo de cada brújula y una altura fija para los títulos.
- **Cada etiqueta en su extremo:** polos del eje X a izquierda y derecha, polos del eje Y arriba y abajo.
- **Trayectoria del código:** un punto por foto, unidos en orden con una curva suave (Catmull-Rom al 60% de tensión: redondea las esquinas sin salirse de los puntos); el último punto más grande, los antiguos más tenues; etiqueta del mes en el primero y en el último.
- **Posición en un eje:**
  - Hacia el valor ganador, normalizado a −1…+1.
  - Distancia al centro proporcional a cuánto mejora frente al extremo contrario: `tanh(ΔWAPE / 5 pp)`, ajustable.
  - Diferencia menor de ~1 pp → zona indiferente, cerca del centro.
- **Selector:** rejilla del mismo tamaño que una brújula (X = amplitud, Y = criterio) con 17 celdas que muestran el nº de códigos del grupo (más oscuro = grupo más grande). La celda elegida lleva recuadro. Encima va la trayectoria del grupo ganador foto a foto, igual que en las brújulas. Debajo, el ganador de cada foto. Tooltip con el WAPE del grupo.
- **Mapa de calor** (interruptor en la cabecera de Decisiones, apagado por defecto): densidad de **los mismos puntos que se dibujan** (cada código × foto en un grupo, cada foto en un código), calculada en una rejilla de 1 px (histograma + gaussiana separable, radio según el nº de puntos) y con escala logarítmica para que un montón de puntos apilados no esconda el resto de la nube. Paleta de mapa de calor "turbo" (azul → cian → verde → amarillo → rojo), transparente donde no hay puntos. El selector usa la misma densidad de los puntos repartidos en sus celdas. Con el mapa de calor activo se ocultan los puntos y líneas pequeños de cada código y queda el promedio encima.
- **Transiciones al cambiar de selección:** si un gráfico está a la vista cuando cambia la selección (o se activa el mapa de calor o cambia un filtro), pasa del estado anterior al nuevo: puntos, líneas y celdas se interpolan desde su posición en pantalla con un muelle sin rebote (≈0,5 s); lo nuevo entra con fundido y escala 0,92; lo que se va sale más rápido. En el mapa de burbujas, cada burbuja se desplaza y cambia de tamaño hasta su nuevo sitio (FLIP con WAAPI, solo transform).
- **Construcción al llegar con el scroll:** al abrir un código o grupo, los gráficos que no están en pantalla se quedan con su marco y sin datos y se construyen la primera vez que entran en la vista (una vez por selección): el Consensus frente al rango se dibuja de izquierda a derecha y cada mes aparece cuando el barrido pasa por él; las trayectorias se trazan de la primera foto a la última; los puntos aparecen en orden de foto; el calor y las celdas del selector entran con fundido. Con movimiento reducido, solo un fundido corto.
- **Selección de un grupo (casa, brand, product line):** en las tres brújulas y en el selector, el **punto grande es el promedio simple de las posiciones de todos los códigos del grupo** en cada foto, y su trayectoria se mueve foto a foto. Debajo, cada código del grupo se dibuja con un punto y una línea pequeños; al pasar el puntero por un código se resalta su línea. En el selector, los códigos se reparten dentro de la celda de su grupo ganador. Los valores del pie siguen siendo los de la regla del grupo.

### Sección "Resultados" — rejilla 2 × 2
- Tres **medias brújulas**: SPP3·WAPE90, SPP6·WAPE180, SPP·WAPE(9M).
  - X = SPP (−30% … +30%; izquierda = sobre-forecast). Y = WAPE (0 … 60%, solo cuadrantes superiores).
  - **Zona meta** marcada: WAPE ≤ 40% y SPP ±5%. Línea en WAPE 40%.
  - Dos trayectorias por foto: gris discontinua = lo que pasó (Consensus real), azul = mejor receta. La distancia entre ambas es lo que se habría ganado.
  - Debajo, los valores de la última foto.
- Cuarto cuadro: cómo leerlas.
- Escalas fijas para comparar códigos. Si un valor sale del rango, dibujarlo pegado al borde con un indicador.

### Sección "Detector"
- Tabla de EANs fuera de su estrategia, con desvío en unidades y en %, ordenable, y control para la tolerancia (inicio y fin).
- **Solo los códigos de la selección** (el código, el grupo, el grupo filtrado o la selección acumulada): los cálculos usan toda la casa, pero aquí se ven solo sus resultados.

---

## 10. Pendiente / fuera de fase 1
- Reexport de los CSV con el EAN como texto (lo hace el usuario).
- Confirmar la ventana de la "media" de la base (propuesta: 12M).
- Diferenciar tipos de promo dentro de la Total Demand Assumption (2ª etapa).
- Escritura de la receta elegida en `Reasonability Adjustment` (más adelante).
- Análisis de tendencias y patrones entre fotos (se define después).

## Orden de trabajo sugerido
1. Lector y validador de fotos (formato, EAN, mes de foto, scope, edad, tamaño), con tests sobre `Gucci_2026_04.csv`.
2. Motor de recetas vectorizado, con tests de las fórmulas en casos pequeños calculados a mano.
3. Cubo Parquet, tramos abiertos/cerrados y resúmenes por foto.
4. Score multi-foto y detector.
5. Interfaz.
