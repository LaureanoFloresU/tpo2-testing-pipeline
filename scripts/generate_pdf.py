from pathlib import Path
import re
import textwrap
import zipfile
from html import escape


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "TPO2.md"
PDF_OUTPUT = ROOT / "Flores_1142069_26042026_TPO2.pdf"
HTML_OUTPUT = ROOT / "Flores_1142069_26042026_TPO2.html"
DOCX_OUTPUT = ROOT / "Flores_1142069_26042026_TPO2.docx"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_X = 54
MARGIN_TOP = 58
MARGIN_BOTTOM = 58


def strip_md(text: str) -> str:
    text = text.replace("`", "")
    text = text.replace("**", "")
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", text)
    return text


def markdown_to_blocks(markdown: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    in_code = False
    code_lines: list[str] = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                blocks.append(("code", "\n".join(code_lines)))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            blocks.append(("blank", ""))
        elif line.startswith("# "):
            blocks.append(("h1", strip_md(line[2:])))
        elif line.startswith("## "):
            blocks.append(("h2", strip_md(line[3:])))
        elif line.startswith("### "):
            blocks.append(("h3", strip_md(line[4:])))
        elif line.startswith("- "):
            blocks.append(("p", "- " + strip_md(line[2:])))
        elif re.match(r"^\d+\. ", line):
            blocks.append(("p", strip_md(line)))
        elif line.startswith("|"):
            table_text = " | ".join(part.strip() for part in line.strip("|").split("|"))
            if not set(table_text.replace("|", "").replace("-", "").replace(" ", "")):
                continue
            blocks.append(("p", strip_md(table_text)))
        else:
            blocks.append(("p", strip_md(line)))

    return blocks


def blocks_to_pdf_lines(blocks: list[tuple[str, str]]) -> list[tuple[str, int, str]]:
    lines: list[tuple[str, int, str]] = []
    for kind, text in blocks:
        if kind == "blank":
            lines.append(("", 10, "F1"))
            continue
        if kind == "h1":
            wrap_width, size, font = 50, 17, "F2"
        elif kind == "h2":
            wrap_width, size, font = 64, 13, "F2"
        elif kind == "h3":
            wrap_width, size, font = 70, 11, "F2"
        elif kind == "code":
            wrap_width, size, font = 78, 9, "F1"
        else:
            wrap_width, size, font = 88, 10, "F1"

        wrapped = []
        for part in text.splitlines() or [""]:
            wrapped.extend(textwrap.wrap(part, width=wrap_width, replace_whitespace=False) or [""])
        for part in wrapped:
            lines.append((part, size, font))
        if kind in {"h1", "h2", "h3", "code"}:
            lines.append(("", 8, "F1"))
    return lines


def paginate(lines: list[tuple[str, int, str]]) -> list[list[tuple[str, int, str]]]:
    pages: list[list[tuple[str, int, str]]] = []
    current: list[tuple[str, int, str]] = []
    y = PAGE_HEIGHT - MARGIN_TOP
    for line in lines:
        _, size, _ = line
        step = max(size + 5, 13)
        if y - step < MARGIN_BOTTOM:
            pages.append(current)
            current = []
            y = PAGE_HEIGHT - MARGIN_TOP
        current.append(line)
        y -= step
    if current:
        pages.append(current)
    return pages


def pdf_escape(text: str) -> str:
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def content_stream(page: list[tuple[str, int, str]], page_number: int, total_pages: int) -> str:
    commands: list[str] = []
    y = PAGE_HEIGHT - MARGIN_TOP
    for text, size, font in page:
        step = max(size + 5, 13)
        if text:
            commands.append("BT")
            commands.append(f"/{font} {size} Tf")
            commands.append(f"1 0 0 1 {MARGIN_X} {y} Tm")
            commands.append(f"({pdf_escape(text)}) Tj")
            commands.append("ET")
        y -= step

    commands.append("BT")
    commands.append("/F1 9 Tf")
    commands.append(f"1 0 0 1 {MARGIN_X} 34 Tm")
    commands.append(f"({pdf_escape(f'Pagina {page_number} de {total_pages}')}) Tj")
    commands.append("ET")
    return "\n".join(commands)


def write_pdf(pages: list[list[tuple[str, int, str]]]) -> None:
    objects: list[str] = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")

    first_page_obj = 3
    font_regular_obj = first_page_obj + len(pages) * 2
    font_bold_obj = font_regular_obj + 1
    kids = " ".join(f"{first_page_obj + index * 2} 0 R" for index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")

    for index, page in enumerate(pages, start=1):
        page_obj = first_page_obj + (index - 1) * 2
        content_obj = page_obj + 1
        stream = content_stream(page, index, len(pages))
        encoded = stream.encode("latin-1", "replace")
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_regular_obj} 0 R /F2 {font_bold_obj} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        objects.append(f"<< /Length {len(encoded)} >>\nstream\n{stream}\nendstream")

    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))

    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    PDF_OUTPUT.write_bytes(pdf)


def write_html(markdown: str) -> None:
    blocks = markdown_to_blocks(markdown)
    html_parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>TPO2 - Automatizacion de pruebas y pipeline CI/CD</title>",
        "<style>body{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;line-height:1.5;color:#222}"
        "h1,h2,h3{color:#111}code,pre{background:#f3f3f3;padding:2px 4px}"
        "pre{padding:12px;white-space:pre-wrap}p{margin:8px 0}</style></head><body>",
    ]
    for kind, text in blocks:
        safe = escape(text)
        if kind == "blank":
            html_parts.append("<br>")
        elif kind in {"h1", "h2", "h3"}:
            html_parts.append(f"<{kind}>{safe}</{kind}>")
        elif kind == "code":
            html_parts.append(f"<pre>{safe}</pre>")
        else:
            html_parts.append(f"<p>{safe}</p>")
    html_parts.append("</body></html>")
    HTML_OUTPUT.write_text("\n".join(html_parts), encoding="utf-8")


def write_docx(markdown: str) -> None:
    blocks = markdown_to_blocks(markdown)

    def paragraph(text: str, style: str | None = None) -> str:
        style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
        return f"<w:p>{style_xml}<w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p>"

    body = []
    for kind, text in blocks:
        if kind == "blank":
            body.append(paragraph(""))
        elif kind == "h1":
            body.append(paragraph(text, "Title"))
        elif kind == "h2":
            body.append(paragraph(text, "Heading1"))
        elif kind == "h3":
            body.append(paragraph(text, "Heading2"))
        elif kind == "code":
            for line in text.splitlines():
                body.append(paragraph(line))
        else:
            body.append(paragraph(text))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        + "".join(body)
        + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" '
        'w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/>'
        '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/>'
        '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/>'
        '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
        "</w:styles>"
    )

    with zipfile.ZipFile(DOCX_OUTPUT, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/styles.xml", styles)


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    blocks = markdown_to_blocks(markdown)
    pages = paginate(blocks_to_pdf_lines(blocks))
    write_pdf(pages)
    write_html(markdown)
    write_docx(markdown)
    print(f"PDF generado: {PDF_OUTPUT}")
    print(f"HTML generado: {HTML_OUTPUT}")
    print(f"DOCX generado: {DOCX_OUTPUT}")


if __name__ == "__main__":
    main()
