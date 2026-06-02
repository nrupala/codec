"""Generate HTML and PDF documentation from markdown sources."""

import markdown
import os
import sys
from datetime import datetime
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
OUTPUT_DIR = DOCS_DIR / "_build"


def markdown_to_html(md_content: str) -> str:
    extensions = [
        "markdown.extensions.fenced_code",
        "markdown.extensions.codehilite",
        "markdown.extensions.tables",
        "markdown.extensions.toc",
        "markdown.extensions.smarty",
    ]
    return markdown.markdown(md_content, extensions=extensions)


def wrap_html(title: str, body: str) -> str:
    styles = """
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
        line-height: 1.6; color: #1f2328; max-width: 900px; margin: 0 auto; padding: 40px 24px;
      }
      h1 { font-size: 2em; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; margin-bottom: 16px; }
      h2 { font-size: 1.5em; border-bottom: 1px solid #d0d7de; padding-bottom: 6px; margin: 24px 0 12px; }
      h3 { font-size: 1.25em; margin: 20px 0 8px; }
      p { margin: 0 0 12px; }
      a { color: #0969da; text-decoration: none; }
      a:hover { text-decoration: underline; }
      code { background: #f6f8fa; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }
      pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; margin: 12px 0; border: 1px solid #d0d7de; }
      pre code { background: none; padding: 0; }
      table { width: 100%; border-collapse: collapse; margin: 12px 0; }
      th, td { border: 1px solid #d0d7de; padding: 8px 12px; text-align: left; }
      th { background: #f6f8fa; font-weight: 600; }
      ul, ol { padding-left: 24px; margin: 8px 0; }
      blockquote { border-left: 4px solid #d0d7de; padding: 8px 16px; margin: 12px 0; color: #656d76; background: #f6f8fa; }
      hr { border: none; border-top: 1px solid #d0d7de; margin: 24px 0; }
      .footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid #d0d7de; font-size: 0.9em; color: #656d76; }
    </style>
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title}</title>{styles}</head>
<body>{body}<div class="footer">CodeC Documentation -- Generated {date_str}</div></body>
</html>"""


def generate_html():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    md_files = list(DOCS_DIR.glob("*.md"))
    readme = DOCS_DIR.parent / "README.md"
    if readme.exists():
        md_files.insert(0, readme)

    for md_file in md_files:
        if md_file.name == "_build":
            continue
        title = md_file.stem.replace("-", " ").title()
        content = md_file.read_text(encoding="utf-8")
        body = markdown_to_html(content)
        html = wrap_html(title, body)
        out_file = OUTPUT_DIR / f"{md_file.stem}.html"
        out_file.write_text(html, encoding="utf-8")
        print(f"  OK {out_file.name}")

    index_body = "<h1>CodeC Documentation</h1><ul>"
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        name = md_file.stem.replace("-", " ").title()
        index_body += f'<li><a href="{md_file.stem}.html">{name}</a></li>'
    index_body += '<li><a href="../README.html">Readme</a></li></ul>'
    (OUTPUT_DIR / "index.html").write_text(
        wrap_html("Documentation Index", index_body), encoding="utf-8"
    )
    print("  OK index.html")


def generate_pdf():
    try:
        from weasyprint import HTML
        has_weasy = True
    except ImportError:
        has_weasy = False

    try:
        import pdfkit
        has_pdfkit = True
    except ImportError:
        has_pdfkit = False

    if not has_weasy and not has_pdfkit:
        print("  PDF skipped: install weasyprint or pdfkit")
        return

    for html_file in sorted(OUTPUT_DIR.glob("*.html")):
        pdf_file = OUTPUT_DIR / f"{html_file.stem}.pdf"
        try:
            if has_weasy:
                HTML(filename=str(html_file)).write_pdf(str(pdf_file))
            else:
                pdfkit.from_file(str(html_file), str(pdf_file))
            print(f"  OK {pdf_file.name}")
        except Exception as e:
            print(f"  FAIL {pdf_file.name}: {e}")


def main():
    print("Generating HTML...")
    generate_html()
    print("Generating PDF...")
    generate_pdf()
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
