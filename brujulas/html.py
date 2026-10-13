import json
from pathlib import Path
def generar_html(datos, ruta):
    plantilla = Path(__file__).with_name("plantilla.html").read_text(encoding="utf-8")
    txt = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    Path(ruta).write_text(plantilla.replace("/*__DATOS__*/null", txt), encoding="utf-8")
    return ruta
