from pathlib import Path
import re
import textwrap


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "TPO2.md"
OUTPUT = ROOT / "Flores_1142069_26042026_TPO2.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_X = 54
MARGIN_TOP = 58
MARGIN_BOTTOM = 58
LINE_HEIGHT = 14
CHARS_PER_LINE = 88


def clean_markdown(line: str) -> tuple[str, int]:
    level = 0
    if line.startswith("# "):
        level = 1
        line = line[2:]
    elif line.startswith("## "):
        level = 2
        line = line[3:]
    elif line.startswith("### "):
        level = 3
        line = line[4:]

    line = line.replace("`", "")
    line = line.replace("**", "")
    line = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", line)
    return line.rstrip(), level


def build_lines(markdown: str) -> list[tuple[str, int]]:
    lines: list[tuple[str, int]] = []
    in_code = False

    for raw in markdown.splitlines():
        if raw.strip().startswith("```"):
            in_code = not in_code
            lines.append(("", 0))
            continue

        text, level = clean_markdown(raw)
        if not text:
            lines.append(("", 0))
            continue

        if in_code:
            wrapped = textwrap.wrap(text, width=80, replace_whitespace=False) or [text]
            lines.extend((f"    {part}", 0) for part in wrapped)
            continue

        if text.startswith("|"):
            text = re.sub(r"\s*\|\s*", " | ", text.strip("| "))

        width = 58 if level == 1 else 70 if level in (2, 3) else CHARS_PER_LINE
        for part in textwrap.wrap(text, width=width):
            lines.append((part, level))

    return lines


def paginate(lines: list[tuple[str, int]]) -> list[list[tuple[str, int]]]:
    pages: list[list[tuple[str, int]]] = []
    current: list[tuple[str, int]] = []
    y = MARGIN_TOP

    for text, level in lines:
        extra = 8 if level == 1 else 5 if level in (2, 3) else 0
        needed = LINE_HEIGHT + extra
        if y + needed > PAGE_HEIGHT - MARGIN_BOTTOM:
            pages.append(current)
            current = []
            y = MARGIN_TOP
        current.append((text, level))
        y += needed

    if current:
        pages.append(current)
    return pages


def pdf_escape(text: str) -> str:
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def content_stream(page: list[tuple[str, int]], page_number: int, total_pages: int) -> str:
    commands = ["BT"]
    y = PAGE_HEIGHT - MARGIN_TOP

    for text, level in page:
        if not text:
            y -= LINE_HEIGHT
            continue

        if level == 1:
            size = 18
            font = "F2"
            y -= 8
        elif level in (2, 3):
            size = 13
            font = "F2"
            y -= 5
        else:
            size = 10
            font = "F1"

        commands.append(f"/{font} {size} Tf")
        commands.append(f"{MARGIN_X} {y} Td ({pdf_escape(text)}) Tj")
        commands.append(f"{-MARGIN_X} {-LINE_HEIGHT} Td")
        y -= LINE_HEIGHT

    footer = f"Pagina {page_number} de {total_pages}"
    commands.append("/F1 9 Tf")
    commands.append(f"{MARGIN_X} {MARGIN_BOTTOM - 20} Td ({pdf_escape(footer)}) Tj")
    commands.append("ET")
    return "\n".join(commands)


def write_pdf(pages: list[list[tuple[str, int]]]) -> None:
    objects: list[str] = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")

    page_objects = []
    content_objects = []
    first_page_obj = 3
    for index in range(len(pages)):
        page_obj = first_page_obj + index * 2
        content_obj = page_obj + 1
        page_objects.append(page_obj)
        content_objects.append(content_obj)

    kids = " ".join(f"{obj} 0 R" for obj in page_objects)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")

    total = len(pages)
    for index, page in enumerate(pages, start=1):
        content = content_stream(page, index, total)
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {first_page_obj + total * 2} 0 R "
            f"/F2 {first_page_obj + total * 2 + 1} 0 R >> >> "
            f"/Contents {first_page_obj + (index - 1) * 2 + 1} 0 R >>"
        )
        objects.append(f"<< /Length {len(content.encode('latin-1', 'replace'))} >>\nstream\n{content}\nendstream")

    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    pdf = bytearray(b"%PDF-1.4\n")
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

    OUTPUT.write_bytes(pdf)


def main() -> None:
    lines = build_lines(SOURCE.read_text(encoding="utf-8"))
    pages = paginate(lines)
    write_pdf(pages)
    print(f"PDF generado: {OUTPUT}")


if __name__ == "__main__":
    main()

