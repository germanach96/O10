import json
from pathlib import Path


def generar_html(datos, ruta):
    aqui = Path(__file__).parent
    plantilla = (aqui / "plantilla.html").read_text(encoding="utf-8")
    # d3-hierarchy (ISC, Mike Bostock) va incrustado: la página se abre sin servidor ni red
    d3h = (aqui / "vendor" / "d3-hierarchy.min.js").read_text(encoding="utf-8")
    txt = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    # versión visible en la página (archivo VERSION en la raíz: O10.0.1, O10.0.2…)
    version = (aqui.parent / "VERSION").read_text(encoding="utf-8").strip()
    plantilla = plantilla.replace("__VERSION__", version)
    html = plantilla.replace("/*__D3H__*/", d3h.replace("</", "<\\/")).replace("/*__DATOS__*/null", txt)
    Path(ruta).write_text(html, encoding="utf-8")
    return ruta
