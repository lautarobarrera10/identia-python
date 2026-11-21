"""
Página con el formulario para cargar las urls y generar el reporte.
"""

from html import escape

from identia_python.reporte_html import ESTILOS

RUTA_REPORTE = "/reporte"

ESTILOS_FORMULARIO = """
form { display: grid; gap: 14px; }
textarea {
  width: 100%; min-height: 260px; padding: 12px; resize: vertical;
  background: var(--tarjeta); color: var(--texto); border: 1px solid var(--borde);
  border-radius: 10px; font: .9rem/1.5 ui-monospace, Consolas, monospace;
}
label.opcion { display: flex; gap: 8px; align-items: center; color: var(--suave); }
button {
  justify-self: start; padding: 10px 20px; border: 0; border-radius: 8px;
  background: var(--link); color: #fff; font: inherit; font-weight: 600;
  cursor: pointer;
}
button:disabled { opacity: .6; cursor: progress; }
.aviso {
  background: var(--error-fondo); color: var(--error); font-weight: 600;
  padding: 10px 14px; border-radius: 8px; margin: 0 0 16px;
}
"""

# Deshabilita el botón al enviar: procesar las noticias tarda unos segundos
SCRIPT = """
document.querySelector("form").addEventListener("submit", (e) => {
  const boton = e.target.querySelector("button");
  boton.disabled = true;
  boton.textContent = "Procesando…";
});
"""


def generar_formulario(error: str | None = None, urls: str = "") -> str:
    """Arma la página del formulario; si hay error lo muestra arriba."""
    aviso = f'<p class="aviso">{escape(error)}</p>' if error else ""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Generar reporte</title>
<style>{ESTILOS}{ESTILOS_FORMULARIO}</style>
</head>
<body>
<main>
<h1>Generar reporte</h1>
<p class="meta">Pegá las urls de las noticias, una por línea. Las líneas vacías,
las que empiezan con # y las repetidas se ignoran.</p>
{aviso}
<form method="post" action="{RUTA_REPORTE}">
<textarea name="urls" placeholder="https://www.ejemplo.com/noticia"
 required autofocus>{escape(urls)}</textarea>
<label class="opcion"><input type="checkbox" name="forzar" value="1">
Ignorar el caché y volver a procesar todas las urls</label>
<button type="submit">Generar reporte</button>
</form>
</main>
<script>{SCRIPT}</script>
</body>
</html>
"""
