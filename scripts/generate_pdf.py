from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
import textwrap
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "TPO2.md"
PDF_OUTPUT = ROOT / "Flores_1142069_28042026_TPO2.pdf"
HTML_OUTPUT = ROOT / "Flores_1142069_28042026_TPO2.html"
DOCX_OUTPUT = ROOT / "Flores_1142069_28042026_TPO2.docx"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_X = 56
MARGIN_TOP = 58
MARGIN_BOTTOM = 58


@dataclass
class Block:
    kind: str
    text: str = ""
    bookmark: str | None = None


@dataclass
class PdfLine:
    text: str
    size: int
    font: str
    kind: str = "text"
    bookmark: str | None = None
    target: str | None = None


def strip_md(text: str) -> str:
    text = text.replace("`", "")
    text = text.replace("**", "")
    return re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", text)


def bookmark_for(text: str) -> str:
    match = re.match(r"^(\d+)\.", text.strip())
    if match:
        return f"Sec{match.group(1)}"
    slug = re.sub(r"[^A-Za-z0-9]+", "", text.title())
    return (slug or "Section")[:32]


def parse_table_row(line: str) -> list[str]:
    return [strip_md(part.strip()) for part in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", line))


def append_block(blocks: list[Block], block: Block) -> None:
    if block.kind == "blank" and (not blocks or blocks[-1].kind in {"blank", "pagebreak", "h1", "h2", "h3"}):
        return
    blocks.append(block)


def markdown_to_blocks(markdown: str) -> list[Block]:
    blocks: list[Block] = []
    in_code = False
    in_index = False
    code_lines: list[str] = []
    lines = markdown.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index].rstrip()
        if line.strip() == "<!-- pagebreak -->":
            append_block(blocks, Block("pagebreak"))
            in_index = False
            index += 1
            continue
        if line.strip().startswith("```"):
            if in_code:
                append_block(blocks, Block("code", "\n".join(code_lines)))
                code_lines = []
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if line.startswith("|"):
            table_rows: list[list[str]] = []
            while index < len(lines) and lines[index].rstrip().startswith("|"):
                current = lines[index].rstrip()
                if not is_table_separator(current):
                    table_rows.append(parse_table_row(current))
                index += 1
            if table_rows:
                append_block(blocks, Block("table", "\n".join("\t".join(row) for row in table_rows)))
            continue
        if not line.strip():
            append_block(blocks, Block("blank"))
        elif line.startswith("# "):
            append_block(blocks, Block("h1", strip_md(line[2:])))
        elif line.startswith("## "):
            text = strip_md(line[3:])
            if text == "Indice":
                in_index = True
            append_block(blocks, Block("h2", text, bookmark_for(text)))
        elif line.startswith("!["):
            match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if match:
                append_block(blocks, Block("image", f"{match.group(1)}\t{match.group(2)}"))
            else:
                append_block(blocks, Block("p", strip_md(line)))
        elif line.startswith("### "):
            append_block(blocks, Block("h3", strip_md(line[4:])))
        elif line.startswith("- "):
            append_block(blocks, Block("p", "- " + strip_md(line[2:])))
        elif in_index and re.match(r"^\d+\. ", line):
            append_block(blocks, Block("toc", strip_md(line), bookmark_for(line)))
        elif re.match(r"^\d+\. ", line):
            append_block(blocks, Block("p", strip_md(line)))
        else:
            append_block(blocks, Block("p", strip_md(line)))
        index += 1
    return blocks


def blocks_to_pdf_lines(blocks: list[Block]) -> list[PdfLine]:
    lines: list[PdfLine] = []
    for block in blocks:
        if block.kind == "pagebreak":
            lines.append(PdfLine("__PAGEBREAK__", 0, "PAGEBREAK"))
            continue
        if block.kind == "blank":
            lines.append(PdfLine("", 10, "F1"))
            continue
        if block.kind == "h1":
            width, size, font = 48, 18, "F2"
        elif block.kind == "h2":
            width, size, font = 64, 14, "F2"
        elif block.kind == "h3":
            width, size, font = 72, 12, "F2"
        elif block.kind == "toc":
            width, size, font = 80, 11, "F1"
        elif block.kind == "code":
            width, size, font = 80, 9, "F1"
        elif block.kind == "table":
            for row_index, row in enumerate(block.text.splitlines()):
                lines.append(PdfLine(row, 8, "F2" if row_index == 0 else "F1", kind="table_header" if row_index == 0 else "table_row"))
            lines.append(PdfLine("", 8, "F1"))
            continue
        elif block.kind == "image":
            caption, path = block.text.split("\t", 1)
            lines.append(PdfLine(f"[Imagen: {caption}]", 10, "F2"))
            lines.append(PdfLine(f"Archivo de evidencia: {path}", 9, "F1"))
            lines.append(PdfLine("", 8, "F1"))
            continue
        else:
            width, size, font = 88, 10, "F1"

        wrapped: list[str] = []
        for part in block.text.splitlines() or [""]:
            wrapped.extend(textwrap.wrap(part, width=width, replace_whitespace=False) or [""])
        for index, part in enumerate(wrapped):
            lines.append(
                PdfLine(
                    part,
                    size,
                    font,
                    kind=block.kind,
                    bookmark=block.bookmark if index == 0 else None,
                    target=block.bookmark if block.kind == "toc" and index == 0 else None,
                )
            )
        if block.kind in {"h1", "h2", "h3", "code"}:
            lines.append(PdfLine("", 8, "F1"))
    return lines


def paginate(lines: list[PdfLine]) -> list[list[PdfLine]]:
    pages: list[list[PdfLine]] = []
    current: list[PdfLine] = []
    y = PAGE_HEIGHT - MARGIN_TOP
    for line in lines:
        if line.font == "PAGEBREAK":
            if current:
                pages.append(current)
                current = []
            y = PAGE_HEIGHT - MARGIN_TOP
            continue
        step = 30 if line.kind in {"table_header", "table_row"} else max(line.size + 5, 13)
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


def text_width(text: str, size: int) -> int:
    return min(int(len(text) * size * 0.55) + 8, PAGE_WIDTH - MARGIN_X * 2)


def cover_stream(total_pages: int) -> str:
    lines = [
        "0.10 0.16 0.24 rg",
        f"0 0 {PAGE_WIDTH} {PAGE_HEIGHT} re f",
        "0.00 0.55 0.70 rg",
        f"0 0 16 {PAGE_HEIGHT} re f",
        "0.95 0.97 0.98 rg",
        "BT /F2 28 Tf 1 0 0 1 70 610 Tm (TPO2) Tj ET",
        "BT /F2 20 Tf 1 0 0 1 70 575 Tm (Automatizacion de pruebas y pipeline CI/CD) Tj ET",
        "BT /F1 13 Tf 1 0 0 1 70 500 Tm (Testing de Aplicaciones \\(14883\\)) Tj ET",
        "0.00 0.55 0.70 rg",
        "70 455 455 2 re f",
        "0.95 0.97 0.98 rg",
        "BT /F1 12 Tf 1 0 0 1 70 410 Tm (Alumno: Laureano Tomas Flores) Tj ET",
        "BT /F1 12 Tf 1 0 0 1 70 386 Tm (Legajo: 1142069) Tj ET",
        "BT /F1 12 Tf 1 0 0 1 70 362 Tm (Docente: ABEL ISRAEL LAIME HUANCA) Tj ET",
        "BT /F1 12 Tf 1 0 0 1 70 338 Tm (Fecha: 28/04/2026) Tj ET",
        "BT /F1 10 Tf 1 0 0 1 70 96 Tm (Trabajo Practico Obligatorio - Integracion de testing automatizado y CI/CD) Tj ET",
        f"BT /F1 9 Tf 1 0 0 1 70 34 Tm ({pdf_escape(f'Pagina 1 de {total_pages}')}) Tj ET",
    ]
    return "\n".join(lines)


def normal_stream(page: list[PdfLine], page_number: int, total_pages: int) -> tuple[str, list[dict[str, object]]]:
    commands: list[str] = []
    links: list[dict[str, object]] = []
    y = PAGE_HEIGHT - MARGIN_TOP
    for line in page:
        step = 30 if line.kind in {"table_header", "table_row"} else max(line.size + 5, 13)
        if line.text:
            if line.kind in {"table_header", "table_row"}:
                cells = line.text.split("\t")
                col_width = (PAGE_WIDTH - MARGIN_X * 2) / max(len(cells), 1)
                commands.append("0.91 0.95 0.97 rg" if line.kind == "table_header" else "1 1 1 rg")
                commands.append(f"{MARGIN_X} {y - 9} {PAGE_WIDTH - MARGIN_X * 2} 28 re f")
                commands.append("0.65 0.70 0.75 RG")
                for cell_index, cell in enumerate(cells):
                    x = MARGIN_X + col_width * cell_index
                    commands.append(f"{x} {y - 9} {col_width} 28 re S")
                    commands.append("0.08 0.08 0.08 rg")
                    commands.append("BT")
                    commands.append(f"/{line.font} {line.size} Tf")
                    commands.append(f"1 0 0 1 {x + 4} {y + 7} Tm")
                    commands.append(f"({pdf_escape(textwrap.shorten(cell, width=max(int(col_width / 4), 12), placeholder='...'))}) Tj")
                    commands.append("ET")
                y -= step
                continue
            if line.target:
                commands.append("0.00 0.28 0.65 rg")
            else:
                commands.append("0.08 0.08 0.08 rg")
            commands.append("BT")
            commands.append(f"/{line.font} {line.size} Tf")
            commands.append(f"1 0 0 1 {MARGIN_X} {y} Tm")
            commands.append(f"({pdf_escape(line.text)}) Tj")
            commands.append("ET")
            if line.target:
                links.append(
                    {
                        "target": line.target,
                        "rect": [MARGIN_X, y - 3, MARGIN_X + text_width(line.text, line.size), y + line.size + 2],
                    }
                )
        y -= step

    commands.append("0.35 0.35 0.35 rg")
    commands.append("BT /F1 9 Tf")
    commands.append(f"1 0 0 1 {MARGIN_X} 34 Tm")
    commands.append(f"({pdf_escape(f'Pagina {page_number} de {total_pages}')}) Tj")
    commands.append("ET")
    return "\n".join(commands), links


def write_pdf(pages: list[list[PdfLine]]) -> None:
    page_obj_nums = [3 + i * 2 for i in range(len(pages))]
    destination_pages: dict[str, int] = {}
    for page_index, page in enumerate(pages):
        for line in page:
            if line.bookmark and line.kind == "h2":
                destination_pages[line.bookmark] = page_obj_nums[page_index]

    page_streams: list[str] = []
    page_links: list[list[dict[str, object]]] = []
    for index, page in enumerate(pages, start=1):
        if index == 1:
            page_streams.append(cover_stream(len(pages)))
            page_links.append([])
        else:
            stream, links = normal_stream(page, index, len(pages))
            page_streams.append(stream)
            page_links.append(links)

    next_obj = 3 + len(pages) * 2
    annotation_objects: list[tuple[int, str]] = []
    annots_by_page: list[list[int]] = [[] for _ in pages]
    for page_index, links in enumerate(page_links):
        for link in links:
            target = str(link["target"])
            if target not in destination_pages:
                continue
            x1, y1, x2, y2 = link["rect"]  # type: ignore[misc]
            obj_num = next_obj
            next_obj += 1
            annots_by_page[page_index].append(obj_num)
            annotation_objects.append(
                (
                    obj_num,
                    "<< /Type /Annot /Subtype /Link "
                    f"/Rect [{x1} {y1} {x2} {y2}] /Border [0 0 0] "
                    f"/A << /S /GoTo /D [{destination_pages[target]} 0 R /Fit] >> >>",
                )
            )

    font_regular_obj = next_obj
    font_bold_obj = next_obj + 1
    objects: dict[int, str] = {}
    objects[1] = "<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{obj} 0 R" for obj in page_obj_nums)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>"

    for i, stream in enumerate(page_streams):
        page_obj = page_obj_nums[i]
        content_obj = page_obj + 1
        annots = ""
        if annots_by_page[i]:
            annots = "/Annots [" + " ".join(f"{obj} 0 R" for obj in annots_by_page[i]) + "] "
        objects[page_obj] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"{annots}/Resources << /Font << /F1 {font_regular_obj} 0 R /F2 {font_bold_obj} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        encoded = stream.encode("latin-1", "replace")
        objects[content_obj] = f"<< /Length {len(encoded)} >>\nstream\n{stream}\nendstream"

    for obj_num, obj in annotation_objects:
        objects[obj_num] = obj
    objects[font_regular_obj] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    objects[font_bold_obj] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"

    max_obj = max(objects)
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0] * (max_obj + 1)
    for number in range(1, max_obj + 1):
        offsets[number] = len(pdf)
        pdf.extend(f"{number} 0 obj\n{objects[number]}\nendobj\n".encode("latin-1", "replace"))

    xref = len(pdf)
    pdf.extend(f"xref\n0 {max_obj + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for number in range(1, max_obj + 1):
        pdf.extend(f"{offsets[number]:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    PDF_OUTPUT.write_bytes(pdf)


def write_html(markdown: str) -> None:
    blocks = markdown_to_blocks(markdown)
    html_parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>TPO2 - Automatizacion de pruebas y pipeline CI/CD</title>",
        "<style>body{font-family:Arial,sans-serif;margin:0;line-height:1.55;color:#222;background:#f5f7fb}"
        ".page{max-width:900px;min-height:980px;margin:24px auto;background:white;padding:64px;box-shadow:0 10px 34px #ccd}"
        ".cover{background:linear-gradient(135deg,#111827,#0f766e);color:white;display:flex;flex-direction:column;justify-content:center}"
        ".cover h1{font-size:54px;margin:0}.cover h2{font-size:30px;margin:12px 0 60px}.meta{border-top:2px solid #5eead4;padding-top:28px}"
        "h1,h2,h3{color:#111827}.cover h1,.cover h2{color:white}a{color:#075985;text-decoration:none;font-weight:600}"
        "pre{background:#f3f4f6;padding:12px;white-space:pre-wrap;border-left:4px solid #0f766e}"
        "table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}th,td{border:1px solid #cbd5e1;padding:8px;text-align:left;vertical-align:top}th{background:#eaf3f5}"
        "p{margin:8px 0}.break{page-break-after:always}@media print{.page{box-shadow:none;margin:0;page-break-after:always}}</style></head><body>",
        "<section class='page cover'><h1>TPO2</h1><h2>Automatizacion de pruebas y pipeline CI/CD</h2>"
        "<div class='meta'><p><strong>Alumno:</strong> Laureano Tomás Flores</p><p><strong>Legajo:</strong> 1142069</p>"
        "<p><strong>Materia:</strong> Testing de Aplicaciones (14883)</p><p><strong>Docente:</strong> ABEL ISRAEL LAIME HUANCA</p>"
        "<p><strong>Fecha:</strong> 28/04/2026</p></div></section>",
    ]
    page_open = False
    for block in blocks:
        if block.kind == "h1" and block.text in {"Portada", "TPO2 - Automatizacion de pruebas y pipeline CI/CD"}:
            continue
        if block.kind == "pagebreak":
            if page_open:
                html_parts.append("</section>")
                page_open = False
            continue
        if not page_open:
            html_parts.append("<section class='page'>")
            page_open = True
        safe = escape(block.text)
        if block.kind == "blank":
            html_parts.append("<br>")
        elif block.kind == "h2":
            html_parts.append(f"<h2 id='{block.bookmark}'>{safe}</h2>")
        elif block.kind == "h3":
            html_parts.append(f"<h3>{safe}</h3>")
        elif block.kind == "toc":
            html_parts.append(f"<p><a href='#{block.bookmark}'>{safe}</a></p>")
        elif block.kind == "code":
            html_parts.append(f"<pre>{safe}</pre>")
        elif block.kind == "table":
            rows = [row.split("\t") for row in block.text.splitlines()]
            html_parts.append("<table>")
            for row_index, row in enumerate(rows):
                tag = "th" if row_index == 0 else "td"
                html_parts.append("<tr>" + "".join(f"<{tag}>{escape(cell)}</{tag}>" for cell in row) + "</tr>")
            html_parts.append("</table>")
        elif block.kind == "image":
            caption, path = block.text.split("\t", 1)
            html_parts.append(f"<figure><img src='{escape(path)}' alt='{escape(caption)}' style='max-width:100%;border:1px solid #cbd5e1'><figcaption>{escape(caption)}</figcaption></figure>")
        else:
            html_parts.append(f"<p>{safe}</p>")
    if page_open:
        html_parts.append("</section>")
    html_parts.append("</body></html>")
    HTML_OUTPUT.write_text("\n".join(html_parts), encoding="utf-8")


def write_docx(markdown: str) -> None:
    blocks = markdown_to_blocks(markdown)

    def text_run(text: str) -> str:
        return f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'

    def paragraph(text: str, style: str | None = None, bookmark: str | None = None, link: str | None = None) -> str:
        style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
        body = text_run(text)
        if link:
            body = f'<w:hyperlink w:anchor="{link}"><w:r><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:hyperlink>'
        if bookmark:
            bookmark_id = re.sub(r"\D", "", bookmark) or "99"
            body = f'<w:bookmarkStart w:id="{bookmark_id}" w:name="{bookmark}"/>{body}<w:bookmarkEnd w:id="{bookmark_id}"/>'
        return f"<w:p>{style_xml}{body}</w:p>"

    body = [
        paragraph("TPO2", "Title"),
        paragraph("Automatizacion de pruebas y pipeline CI/CD", "Subtitle"),
        paragraph(""),
        paragraph("Alumno: Laureano Tomás Flores"),
        paragraph("Legajo: 1142069"),
        paragraph("Materia: Testing de Aplicaciones (14883)"),
        paragraph("Docente: ABEL ISRAEL LAIME HUANCA"),
        paragraph("Fecha: 28/04/2026"),
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>',
    ]
    for block in blocks:
        if block.kind == "h1" and block.text in {"Portada", "TPO2 - Automatizacion de pruebas y pipeline CI/CD"}:
            continue
        if block.kind == "pagebreak":
            body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        elif block.kind == "blank":
            body.append(paragraph(""))
        elif block.kind == "h2":
            body.append(paragraph(block.text, "Heading1", bookmark=block.bookmark))
        elif block.kind == "h3":
            body.append(paragraph(block.text, "Heading2"))
        elif block.kind == "toc":
            body.append(paragraph(block.text, link=block.bookmark))
        elif block.kind == "code":
            for line in block.text.splitlines():
                body.append(paragraph(line))
        elif block.kind == "table":
            rows = [row.split("\t") for row in block.text.splitlines()]
            table_rows = []
            for row in rows:
                cells = "".join(
                    "<w:tc><w:tcPr><w:tcW w:w=\"2400\" w:type=\"dxa\"/></w:tcPr>"
                    f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(cell)}</w:t></w:r></w:p></w:tc>"
                    for cell in row
                )
                table_rows.append(f"<w:tr>{cells}</w:tr>")
            body.append(
                "<w:tbl><w:tblPr><w:tblBorders>"
                "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"B8C2CC\"/>"
                "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"B8C2CC\"/>"
                "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"B8C2CC\"/>"
                "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"B8C2CC\"/>"
                "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"B8C2CC\"/>"
                "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"B8C2CC\"/>"
                "</w:tblBorders></w:tblPr>"
                + "".join(table_rows)
                + "</w:tbl>"
            )
        elif block.kind == "image":
            caption, path = block.text.split("\t", 1)
            body.append(paragraph(f"Captura: {caption}"))
            body.append(paragraph(f"Archivo de evidencia: {path}"))
        else:
            body.append(paragraph(block.text))

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
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
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
        '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="44"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:rPr><w:sz w:val="28"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
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
    write_pdf(paginate(blocks_to_pdf_lines(blocks)))
    write_html(markdown)
    write_docx(markdown)
    print(f"PDF generado: {PDF_OUTPUT}")
    print(f"HTML generado: {HTML_OUTPUT}")
    print(f"DOCX generado: {DOCX_OUTPUT}")


if __name__ == "__main__":
    main()
