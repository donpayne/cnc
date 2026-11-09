"""Prints TOOLS.md to TOOLS.pdf on landscape letter pages, for the shop.

Markdown has no page orientation, so this renders the sheet to HTML with a landscape @page rule and has headless
Chrome print it. Needs the `markdown` package and Google Chrome.

Usage: python3 tools_pdf.py, with a Python that has `markdown` (on this Mac, /opt/homebrew/bin/python3.11).
Rerun it after editing TOOLS.md.
"""
import pathlib
import re
import subprocess
import tempfile

import markdown

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "TOOLS.md"
OUTPUT = HERE / "TOOLS.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

STYLE = """
@page { size: letter landscape; margin: 12mm; }
body { font: 10pt -apple-system, Helvetica, Arial, sans-serif; color: #111; }
h1 { font-size: 16pt; margin: 0 0 6pt; }
h2 { font-size: 13pt; margin: 14pt 0 4pt; border-bottom: 1px solid #999; }
h3 { font-size: 11pt; margin: 10pt 0 4pt; }
p, li { margin: 3pt 0; line-height: 1.3; }
table { border-collapse: collapse; margin: 6pt 0; page-break-inside: avoid; }
th, td { border: 1px solid #999; padding: 3pt 8pt; text-align: left; white-space: nowrap; }
th { background: #e8e8e8; }
tr:nth-child(even) td { background: #f6f6f6; }
code { font-size: 9pt; }
section { break-inside: avoid; }
"""


def keep_sections_together(body):
    """Wraps each heading and what follows it, up to the next heading, so a page break can't strand a heading."""
    chunks = re.split(r"(?=<h[23]>)", body)
    return "".join(f"<section>{chunk}</section>" if chunk.startswith("<h") else chunk for chunk in chunks)


def render_html(markdown_text):
    body = keep_sections_together(markdown.markdown(markdown_text, extensions=["tables"]))
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{STYLE}</style></head><body>{body}</body></html>"


def print_pdf(html, output_path):
    with tempfile.TemporaryDirectory() as folder:
        html_path = pathlib.Path(folder) / "tools.html"
        html_path.write_text(html, encoding="utf-8")
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={output_path}",
             html_path.as_uri()],
            check=True, capture_output=True,
        )


if __name__ == "__main__":
    print_pdf(render_html(SOURCE.read_text(encoding="utf-8")), OUTPUT)
    print(OUTPUT)
