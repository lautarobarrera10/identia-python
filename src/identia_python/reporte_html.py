"""
Generación del contenido del reporte HTML con los resultados.
"""

import json
from collections.abc import Sequence
from datetime import datetime
from html import escape
from urllib.parse import quote

from identia_python.modelos import Articulo
from identia_python.resumen import texto_resumen

ESTILOS = """
:root {
  --fondo: #f6f7f9; --tarjeta: #ffffff; --texto: #1d2330; --suave: #5b6475;
  --borde: #e2e5ea; --link: #1a5fb4; --error: #b42318; --error-fondo: #fdecea;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #14171c; --tarjeta: #1d2128; --texto: #e6e8eb; --suave: #9aa3b2;
    --borde: #2c323c; --link: #78aeff; --error: #ff8a80; --error-fondo: #3a1f1f;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 32px 16px; background: var(--fondo); color: var(--texto);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 820px; margin: 0 auto; }
h1 { margin: 0 0 4px; font-size: 1.6rem; }
.meta { color: var(--suave); margin: 0 0 24px; }
article {
  background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 10px;
  padding: 18px 20px; margin-bottom: 16px;
}
article.error { background: var(--error-fondo); }
.numero { color: var(--suave); font-size: .85rem; }
h2 { margin: 4px 0 8px; font-size: 1.2rem; line-height: 1.3; }
a.url { color: var(--link); font-size: .85rem; word-break: break-all; }
p { margin: 10px 0 0; }
.fallo { color: var(--error); font-weight: 600; }
a.volver { color: var(--link); display: inline-block; margin-bottom: 16px; }
a.email {
  display: inline-block; margin: 0 0 20px; padding: 8px 16px; border-radius: 8px;
  background: var(--link); color: #fff; font-weight: 600; text-decoration: none;
}
.aviso-email { color: var(--suave); margin: -8px 0 20px; }
"""

# Al hacer clic en el botón copia el reporte con formato (HTML) y en texto plano
# al portapapeles; el enlace sigue su curso y abre Gmail en otra pestaña.
# Se usa el evento "copy" porque es sincrónico: termina antes de que la pestaña
# nueva le quite el foco a esta (navigator.clipboard exige foco).
SCRIPT_EMAIL = """
const datos = JSON.parse(document.getElementById("datos-email").textContent);
const aviso = document.getElementById("aviso-email");
function copiarReporte() {
  let copiado = false;
  const alCopiar = (e) => {
    e.clipboardData.setData("text/html", datos.html);
    e.clipboardData.setData("text/plain", datos.texto);
    e.preventDefault();
    copiado = true;
  };
  document.addEventListener("copy", alCopiar);
  try {
    document.execCommand("copy");
  } finally {
    document.removeEventListener("copy", alCopiar);
  }
  return copiado;
}
document.getElementById("enviar-email").addEventListener("click", () => {
  aviso.textContent = copiarReporte()
    ? "Reporte copiado. En Gmail, pegalo en el cuerpo del mensaje con Ctrl+V."
    : "No se pudo copiar el reporte al portapapeles.";
  aviso.hidden = false;
});
"""


def _tarjeta(i: int, url: str, articulo: Articulo | None) -> str:
    enlace = f'<a class="url" href="{escape(url)}" target="_blank">{escape(url)}</a>'
    if articulo is None:
        return (
            f'<article class="error"><div class="numero">#{i}</div>{enlace}'
            '<p class="fallo">No se pudo procesar esta noticia.</p></article>'
        )
    parrafo = "<br>".join(
        escape(linea) for linea in articulo.primer_parrafo.split("\n")
    )
    return (
        f'<article><div class="numero">#{i}</div>'
        f"<h2>{escape(articulo.titulo)}</h2>{enlace}<p>{parrafo}</p></article>"
    )


def texto_email(
    urls: Sequence[str], resultados: Sequence[Articulo | None], fecha: str
) -> str:
    """Arma el reporte en texto plano, para usarlo como cuerpo de un email."""
    bloques = [
        f"Resultados identia-python\nGenerado el {fecha} · {texto_resumen(resultados)}"
    ]
    for i, (url, articulo) in enumerate(zip(urls, resultados, strict=True), 1):
        if articulo is None:
            bloques.append(f"#{i}\n{url}\nNo se pudo procesar esta noticia.")
        else:
            bloques.append(f"#{i} {articulo.titulo}\n{url}\n{articulo.primer_parrafo}")
    return "\n\n".join(bloques)


def html_email(
    urls: Sequence[str], resultados: Sequence[Articulo | None], fecha: str
) -> str:
    """
    Arma el reporte como HTML para pegar en el cuerpo de un email. Los estilos
    van en línea porque Gmail descarta los bloques <style>.
    """
    partes = [
        '<div style="font-family:Arial,Helvetica,sans-serif;color:#1d2330;'
        'font-size:14px;line-height:1.5">',
        '<h1 style="font-size:20px;margin:0 0 4px">Resultados identia-python</h1>',
        f'<p style="color:#5b6475;margin:0 0 16px">Generado el {escape(fecha)} · '
        f"{escape(texto_resumen(resultados))}</p>",
    ]
    for i, (url, articulo) in enumerate(zip(urls, resultados, strict=True), 1):
        enlace = (
            f'<a href="{escape(url)}" style="color:#1a5fb4;font-size:12px;'
            f'word-break:break-all">{escape(url)}</a>'
        )
        if articulo is None:
            titulo = f"#{i}"
            contenido = (
                '<p style="color:#b42318;font-weight:bold;margin:6px 0 0">'
                "No se pudo procesar esta noticia.</p>"
            )
        else:
            titulo = f"#{i} · {escape(articulo.titulo)}"
            parrafo = "<br>".join(
                escape(linea) for linea in articulo.primer_parrafo.split("\n")
            )
            contenido = f'<p style="margin:6px 0 0">{parrafo}</p>'
        partes.append(
            '<div style="border-top:1px solid #e2e5ea;padding:12px 0">'
            f'<h2 style="font-size:16px;margin:0 0 4px">{titulo}</h2>'
            f"{enlace}{contenido}</div>"
        )
    partes.append("</div>")
    return "".join(partes)


def enlace_gmail(asunto: str) -> str:
    """
    Arma un enlace que abre la ventana de redacción de Gmail en el navegador
    con el asunto cargado (sin destinatario). El cuerpo se pega desde el
    portapapeles, porque la url de Gmail solo admite texto plano.
    """
    return f"https://mail.google.com/mail/?view=cm&fs=1&su={quote(asunto, safe='')}"


def _datos_email_json(html: str, texto: str) -> str:
    """
    Serializa el cuerpo del email para incrustarlo en un <script>. Se escapa
    "<" para que el contenido no pueda cerrar la etiqueta.
    """
    datos = json.dumps({"html": html, "texto": texto}, ensure_ascii=False)
    return datos.replace("<", "\\u003c")


def generar_html(
    urls: Sequence[str],
    resultados: Sequence[Articulo | None],
    volver: str | None = None,
) -> str:
    """
    Arma una página HTML autocontenida con un resultado por url, en orden.
    Si se indica `volver`, agrega arriba un enlace a esa dirección.
    """
    enlace_volver = (
        f'<a class="volver" href="{escape(volver)}">← Nuevo reporte</a>'
        if volver is not None
        else ""
    )
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    resumen = texto_resumen(resultados)
    asunto = f"Reporte identia-python - {fecha}"
    gmail = enlace_gmail(asunto)
    datos_email = _datos_email_json(
        html_email(urls, resultados, fecha), texto_email(urls, resultados, fecha)
    )
    tarjetas = "\n".join(
        _tarjeta(i, url, articulo)
        for i, (url, articulo) in enumerate(zip(urls, resultados, strict=True), 1)
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resultados identia-python</title>
<style>{ESTILOS}</style>
</head>
<body>
<main>
{enlace_volver}
<h1>Resultados</h1>
<p class="meta">Generado el {fecha} · {resumen}</p>
<a class="email" id="enviar-email" href="{escape(gmail)}" target="_blank"
 rel="noopener">✉ Enviar con Gmail</a>
<p class="aviso-email" id="aviso-email" hidden></p>
{tarjetas}
</main>
<script type="application/json" id="datos-email">{datos_email}</script>
<script>{SCRIPT_EMAIL}</script>
</body>
</html>
"""
