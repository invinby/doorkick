from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter

ROOT = Path.cwd()
OUT = ROOT
WORK = ROOT / "work"
SOURCE = OUT / "DoorKick_Hardcore_COMPLETE.md"
COVER_ART = OUT / "assets" / "DoorKick_portal_vector.png"
BODY_PDF = WORK / "DoorKick_full_body.pdf"
COVER_PDF = WORK / "DoorKick_full_cover.pdf"
FINAL_PDF = OUT / "DoorKick_Hardcore_BLUE_COMPLETE.pdf"

INK = HexColor("#05070B")
PAPER = HexColor("#FFFFFF")
WHITE = HexColor("#FFFFFF")
BLUE = HexColor("#075BFF")
ORANGE = BLUE  # Retained internal names; the rendered palette is blue-only.
CYAN = BLUE
MUTED = INK
RULE = INK
SOFT = WHITE
CODE_BG = HexColor("#05070B")
CODE_FG = HexColor("#FFFFFF")

FONT_DIR = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("ArialBold", str(FONT_DIR / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Georgia", str(FONT_DIR / "georgia.ttf")))
pdfmetrics.registerFont(TTFont("GeorgiaBold", str(FONT_DIR / "georgiab.ttf")))
pdfmetrics.registerFont(TTFont("GeorgiaItalic", str(FONT_DIR / "georgiai.ttf")))
pdfmetrics.registerFont(TTFont("GeorgiaBoldItalic", str(FONT_DIR / "georgiaz.ttf")))
pdfmetrics.registerFont(TTFont("Consolas", str(FONT_DIR / "consola.ttf")))
pdfmetrics.registerFontFamily(
    "Georgia", normal="Georgia", bold="GeorgiaBold",
    italic="GeorgiaItalic", boldItalic="GeorgiaBoldItalic",
)
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="ArialBold")

PAGE_W, PAGE_H = A4
LEFT = 66
RIGHT = 61
TOP = 73
BOTTOM = 69
CONTENT_W = PAGE_W - LEFT - RIGHT

styles = {
    "body": ParagraphStyle(
        "body", fontName="Georgia", fontSize=10.05, leading=15.25,
        textColor=INK, spaceAfter=10, alignment=TA_LEFT,
        allowWidows=0, allowOrphans=0,
    ),
    "meta": ParagraphStyle(
        "meta", fontName="Georgia", fontSize=9.7, leading=14.4,
        textColor=INK, spaceAfter=5, keepWithNext=0,
    ),
    "chapter": ParagraphStyle(
        "chapter", fontName="ArialBold", fontSize=30, leading=35,
        textColor=INK, spaceAfter=18, keepWithNext=1,
    ),
    "term": ParagraphStyle(
        "term", fontName="ArialBold", fontSize=17, leading=21,
        textColor=INK, spaceBefore=25, spaceAfter=10, keepWithNext=1,
    ),
    "subhead": ParagraphStyle(
        "subhead", fontName="ArialBold", fontSize=12.6, leading=16.5,
        textColor=INK, spaceBefore=17, spaceAfter=7, keepWithNext=1,
    ),
    "toc_title": ParagraphStyle(
        "toc_title", fontName="ArialBold", fontSize=30, leading=35,
        textColor=INK, spaceAfter=20,
    ),
    "quote": ParagraphStyle(
        "quote", fontName="GeorgiaBold", fontSize=12, leading=18,
        textColor=INK, spaceAfter=0,
    ),
    "code": ParagraphStyle(
        "code", fontName="Consolas", fontSize=8.05, leading=12.4,
        textColor=CODE_FG, spaceAfter=0,
    ),
    "caption": ParagraphStyle(
        "caption", fontName="Arial", fontSize=7.6, leading=10.5,
        textColor=MUTED, spaceBefore=7, spaceAfter=15,
    ),
}

def para_markup(raw: str) -> str:
    pieces = []
    for line in raw.split("\n"):
        safe = html.escape(line.strip())
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"`([^`]+)`", r'<font name="Consolas" color="#075BFF">\1</font>', safe)
        safe = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            r'<link href="\2" color="#075BFF"><u>\1</u></link>',
            safe,
        )
        safe = safe.replace("→", '<font name="Arial">→</font>')
        pieces.append(safe)
    return "<br/>".join(pieces)


class BookDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        if flowable.style.name not in {"chapter", "term"}:
            return
        title = flowable.getPlainText()
        key = "section-%s" % self.seq.nextf("section")
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=0 if flowable.style.name == "chapter" else 1)
        if flowable.style.name == "chapter":
            self.notify("TOCEntry", (0, title, self.page + 1, key))
        elif re.match(r"^\d+\.\d+\s*/", title):
            self.notify("TOCEntry", (1, title, self.page + 1, key))


def page_decor(c, doc):
    c.saveState()
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("ArialBold", 8.2)
    c.drawString(LEFT, PAGE_H - 41, "DOORKICK")
    c.setFont("Arial", 7.7)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_W - RIGHT, PAGE_H - 41, "ОТ МИНУС НУЛЯ ДО SENIOR SECOPS")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.65)
    c.line(LEFT, PAGE_H - 51, PAGE_W - RIGHT, PAGE_H - 51)
    c.line(LEFT, 51, PAGE_W - RIGHT, 51)
    c.setFont("Arial", 7.7)
    c.setFillColor(MUTED)
    c.drawString(LEFT, 34, "DOORKICK / ПОЛНАЯ КНИГА")
    c.setFillColor(ORANGE)
    c.setFont("ArialBold", 10)
    c.drawRightString(PAGE_W - RIGHT, 32, f"{doc.page + 1:02d}")
    c.restoreState()


def draw_cover():
    c = canvas.Canvas(str(COVER_PDF), pagesize=A4)
    image = ImageReader(str(COVER_ART))
    iw, ih = image.getSize()
    scale = max(PAGE_W / iw, PAGE_H / ih)
    dw, dh = iw * scale, ih * scale
    c.setFillColor(INK)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.drawImage(image, (PAGE_W - dw) / 2, (PAGE_H - dh) / 2,
                width=dw, height=dh, mask="auto")

    c.setFillColor(BLUE)
    c.rect(52, PAGE_H - 93, 36, 6, fill=1, stroke=0)
    c.setFont("ArialBold", 12.4)
    c.setFillColor(WHITE)
    c.drawString(52, PAGE_H - 122, "ПОЛЕВОЙ САМОУЧИТЕЛЬ ПО IT И КИБЕРБЕЗОПАСНОСТИ")
    c.setFillColor(WHITE)
    c.setFont("ArialBold", 46)
    c.drawString(48, 145, "DoorKick")
    c.setFont("ArialBold", 13)
    c.drawString(48, 98, "Подними уровень знаний —")
    c.drawString(48, 80, "открой новые возможности.")
    c.setFont("Georgia", 15)
    c.drawString(48, 53, "От минус нуля до Senior SecOps")
    c.setFillColor(WHITE)
    c.setFont("ArialBold", 8.6)
    c.drawString(48, 27, "ПОЛНОЕ ИЗДАНИЕ  /  МОДУЛИ 0–7 + SENIOR SECOPS")
    c.showPage()
    c.save()


class Diagram(Flowable):
    HEIGHTS = {
        "route": 176,
        "packet": 170,
        "transport": 198,
        "request": 180,
        "zones": 191,
        "observability": 180,
        "osi": 270,
        "script": 170,
        "triage": 188,
        "ai": 190,
        "senior": 190,
        "next": 235,
    }

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.width = CONTENT_W
        self.height = self.HEIGHTS[kind]

    def wrap(self, availWidth, availHeight):
        self.width = min(CONTENT_W, availWidth)
        return self.width, self.height

    def line(self, x1, y1, x2, y2, col=CYAN, width=2):
        c = self.canv
        c.setStrokeColor(col)
        c.setLineWidth(width)
        c.line(x1, y1, x2, y2)

    def txt(self, x, y, value, size=9, bold=False, col=INK):
        c = self.canv
        c.setFont("ArialBold" if bold else "Arial", size)
        c.setFillColor(col)
        c.drawString(x, y, value)

    def box(self, x, y, w, h, title, sub="", fill=WHITE, stroke=RULE):
        c = self.canv
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
        c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
        self.txt(x + 10, y + h - 21, title, 10.4, True)
        if sub:
            self.txt(x + 10, y + 14, sub, 7.4, False, MUTED)

    def arrow(self, x1, x2, y, col=ORANGE):
        self.line(x1, y, x2, y, col, 2)
        c = self.canv
        p = c.beginPath()
        p.moveTo(x2, y)
        p.lineTo(x2 - 6, y + 3.5)
        p.lineTo(x2 - 6, y - 3.5)
        p.close()
        c.setFillColor(col)
        c.drawPath(p, fill=1, stroke=0)

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        if self.kind == "next":
            c.setFillColor(INK)
            c.roundRect(0, 16, w, h - 16, 10, fill=1, stroke=0)
            c.setFillColor(ORANGE)
            c.rect(20, h - 43, 35, 5, fill=1, stroke=0)
            self.txt(20, h - 68, "СЛЕДУЮЩАЯ ДВЕРЬ", 9.2, True, WHITE)
            self.txt(20, h - 110, "PoC  /  CVE", 25, True, WHITE)
            self.txt(20, h - 143, "Red Team  /  Blue Team  /  Purple Team", 12, True, WHITE)
            self.txt(20, 55, "Продолжение словаря пойдёт в этой же книге.", 9, False, WHITE)
            self.txt(20, 38, "Точка входа: Proof of Concept.", 8, False, WHITE)
            return
        c.setFillColor(SOFT)
        c.setStrokeColor(INK)
        c.setLineWidth(1)
        c.roundRect(0, 16, w, h - 16, 10, fill=1, stroke=1)
        c.setFillColor(ORANGE)
        c.rect(0, h - 5, 31, 5, fill=1, stroke=0)
        if self.kind == "route":
            self.txt(16, h - 31, "МАРШРУТ КНИГИ", 10.5, True)
            labels = [("01", "СИСТЕМА"), ("02", "СЕТЬ"), ("03", "КОД"),
                      ("04", "ЗАЩИТА"), ("05", "ПРОВЕРКА"), ("06", "ИИ")]
            x = 15
            bw = (w - 30 - 5 * 8) / 6
            for no, lab in labels:
                self.box(x, 63, bw, 72, no, lab, WHITE)
                x += bw + 8
            self.txt(16, 34, "Понимаешь механизм → наблюдаешь → объясняешь → действуешь", 8.1)
        elif self.kind == "packet":
            self.txt(16, h - 31, "СЕТЕВАЯ МАТРЁШКА", 10.5, True)
            widths = [w - 32, w - 78, w - 124, w - 170]
            cols = [INK, CYAN, ORANGE, WHITE]
            labels = ["Ethernet / локальный кадр", "IP / адреса узлов",
                      "TCP / порты и доставка", "HTTP / данные приложения"]
            for i, (bw, col, lab) in enumerate(zip(widths, cols, labels)):
                x = (w - bw) / 2
                y = 37 + i * 24
                c.setFillColor(col)
                c.roundRect(x, y, bw, 34, 5, fill=1, stroke=0)
                self.txt(x + 10, y + 11, lab, 8.5, True, WHITE if i < 3 else INK)
        elif self.kind == "transport":
            self.txt(16, h - 31, "ДВА СПОСОБА ПЕРЕДАЧИ", 10.5, True)
            self.box(16, 100, 67, 46, "TCP", "", WHITE)
            self.box(w - 83, 100, 67, 46, "СЕРВЕР", "", WHITE)
            for y, lab in [(136, "SYN"), (119, "SYN-ACK"), (102, "ACK")]:
                self.arrow(95, w - 94, y, ORANGE if lab != "SYN-ACK" else CYAN)
                self.txt(w / 2 - 24, y + 4, lab, 7.2)
            self.box(16, 31, 67, 45, "UDP", "", WHITE)
            self.box(w - 83, 31, 67, 45, "СЕРВЕР", "", WHITE)
            self.arrow(95, w - 94, 52, CYAN)
            self.txt(w / 2 - 47, 59, "ОДНА ДАТАГРАММА", 7.2)
        elif self.kind == "request":
            self.txt(16, h - 31, "КАК ОТКРЫВАЕТСЯ САЙТ", 10.5, True)
            labels = [("КЛИЕНТ", "браузер"), ("DNS", "имя → IP"),
                      ("МАРШРУТ", "путь"), ("TLS", "защита"),
                      ("HTTP", "запрос"), ("СЕРВЕР", "ответ")]
            x = 15
            bw = (w - 30 - 5 * 7) / 6
            for title, sub in labels:
                self.box(x, 67, bw, 65, title, sub, WHITE)
                x += bw + 7
            self.txt(16, 37, "Сбой на одном шаге не доказывает сбой всех остальных.", 8.2)
        elif self.kind == "zones":
            self.txt(16, h - 31, "ГРАНИЦЫ СЕТИ", 10.5, True)
            bw = (w - 60) / 3
            self.box(15, 70, bw, 69, "ИНТЕРНЕТ", "клиенты", WHITE)
            self.box(30 + bw, 70, bw, 69, "DMZ", "публичный сервис", WHITE)
            self.box(45 + 2 * bw, 70, bw, 69, "ВНУТРИ", "данные и люди", WHITE)
            self.arrow(15 + bw, 30 + bw, 104)
            self.arrow(30 + 2 * bw, 45 + 2 * bw, 104)
            self.txt(16, 39, "Между зонами — конкретные правила, а не вера в название VLAN.", 8.2)
        elif self.kind == "observability":
            self.txt(16, h - 31, "ОТ СОБЫТИЯ К РЕШЕНИЮ", 10.5, True)
            bw = (w - 70) / 3
            self.box(15, 67, bw, 68, "EDR", "события узла", WHITE)
            self.box(35 + bw, 67, bw, 68, "SIEM", "связь журналов", WHITE)
            self.box(55 + 2 * bw, 67, bw, 68, "SOC", "люди и действия", WHITE)
            self.arrow(15 + bw, 35 + bw, 101)
            self.arrow(35 + 2 * bw, 55 + 2 * bw, 101)
            self.txt(16, 37, "Сигнал → контекст → проверенный вывод → реакция.", 8.2)
        elif self.kind == "osi":
            self.txt(16, h - 31, "СЕМЬ УРОВНЕЙ OSI / СНИЗУ ВВЕРХ", 10.5, True)
            levels = [
                ("7", "ПРИЛОЖЕНИЕ", "HTTP, DNS"),
                ("6", "ПРЕДСТАВЛЕНИЕ", "формат данных"),
                ("5", "СЕАНС", "контекст диалога"),
                ("4", "ТРАНСПОРТ", "TCP, UDP / порты"),
                ("3", "СЕТЬ", "IP / маршруты"),
                ("2", "КАНАЛ", "Ethernet / кадры"),
                ("1", "ФИЗИКА", "сигнал и кабель"),
            ]
            for idx, (num, title, detail) in enumerate(levels):
                y = h - 66 - idx * 30
                dark = idx % 2 != 0
                c.setFillColor(INK if dark else WHITE)
                c.roundRect(16, y - 8, w - 32, 27, 5, fill=1, stroke=0)
                fg = WHITE if dark else INK
                self.txt(27, y, num, 10, True, BLUE if not dark else WHITE)
                self.txt(50, y, title, 8.5, True, fg)
                self.txt(w - 153, y, detail, 7.6, False, fg)
        elif self.kind == "script":
            self.txt(16, h - 31, "КОНВЕЙЕР СКРИПТА", 10.5, True)
            labels = [("ВХОД", "файл / API"), ("ПРОВЕРКА", "тип и границы"),
                      ("ОБРАБОТКА", "правила"), ("ВЫХОД", "отчёт")]
            bw = (w - 54) / 4
            for idx, (title, sub) in enumerate(labels):
                x = 15 + idx * (bw + 8)
                self.box(x, 62, bw, 65, title, sub, WHITE)
                if idx < 3:
                    self.arrow(x + bw, x + bw + 8, 95)
            self.txt(16, 34, "Ошибку на входе показывай явно; исходные данные сохраняй.", 8)
        elif self.kind == "triage":
            self.txt(16, h - 31, "МАРШРУТ РАЗБОРА ТРЕВОГИ", 10.5, True)
            labels = [("СИГНАЛ", "что произошло"), ("КОНТЕКСТ", "узел / время"),
                      ("ПРОВЕРКА", "другие источники"), ("РЕШЕНИЕ", "действие")]
            bw = (w - 54) / 4
            for idx, (title, sub) in enumerate(labels):
                x = 15 + idx * (bw + 8)
                self.box(x, 70, bw, 66, title, sub, WHITE)
                if idx < 3:
                    self.arrow(x + bw, x + bw + 8, 103)
            self.txt(16, 39, "Один HTTP 200 или один IOC — гипотеза, не приговор.", 8)
        elif self.kind == "ai":
            self.txt(16, h - 31, "ГРАНИЦА ДОВЕРИЯ В ИИ-ПРИЛОЖЕНИИ", 10.5, True)
            self.box(15, 67, 124, 68, "ПОЛЬЗОВАТЕЛЬ", "законная задача", WHITE)
            self.box(170, 67, 124, 68, "МОДЕЛЬ", "анализ текста", WHITE)
            self.box(325, 67, 124, 68, "ДОКУМЕНТ", "недоверенные данные", WHITE)
            self.arrow(139, 170, 101)
            self.arrow(325, 294, 101, CYAN)
            self.txt(16, 39, "Текст документа не получает права управлять инструментами.", 8)
        elif self.kind == "senior":
            self.txt(16, h - 31, "ЦИКЛ SENIOR SECOPS", 10.5, True)
            labels = [("АКТИВЫ", "что защищаем"), ("ТЕЛЕМЕТРИЯ", "что видим"),
                      ("ДЕТЕКТ", "что заметили"), ("РЕАКЦИЯ", "что сделали")]
            bw = (w - 54) / 4
            for idx, (title, sub) in enumerate(labels):
                x = 15 + idx * (bw + 8)
                self.box(x, 70, bw, 66, title, sub, WHITE)
                if idx < 3:
                    self.arrow(x + bw, x + bw + 8, 103)
            self.txt(16, 39, "После инцидента обнови правила, покрытие и тренировки.", 8)


def code_panel(code: str, lang: str):
    label = Paragraph(
        f'<font color="#075BFF"><b>{html.escape(lang.upper() or "TERMINAL")}</b></font>',
        ParagraphStyle("code-label", fontName="ArialBold", fontSize=7.2, leading=11),
    )
    pre = Preformatted(code.rstrip(), styles["code"])
    tbl = Table([[label], [pre]], colWidths=[CONTENT_W], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BLUE),
        ("BACKGROUND", (0, 1), (0, 1), CODE_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (0, 0), 9),
        ("BOTTOMPADDING", (0, 0), (0, 0), 1),
        ("TOPPADDING", (0, 1), (0, 1), 1),
        ("BOTTOMPADDING", (0, 1), (0, 1), 11),
    ]))
    return KeepTogether([tbl])


def quote_panel(raw: str):
    p = Paragraph(para_markup(raw), styles["quote"])
    tbl = Table([[p]], colWidths=[CONTENT_W], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("LINEBEFORE", (0, 0), (0, -1), 4, BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return tbl


def build_story():
    lines = SOURCE.read_text(encoding="utf-8-sig").splitlines()
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "toc_chapter", fontName="ArialBold", fontSize=11.3, leading=17,
            leftIndent=0, firstLineIndent=0, spaceBefore=11, textColor=INK,
        ),
        ParagraphStyle(
            "toc_section", fontName="Arial", fontSize=9.1, leading=14,
            leftIndent=19, firstLineIndent=0, textColor=MUTED,
        ),
    ]
    story = [Paragraph("Содержание", styles["toc_title"]), toc, PageBreak()]
    i = 0
    started = False
    while i < len(lines):
        s = lines[i].strip()
        if not started:
            if s.startswith("# Введение"):
                started = True
            else:
                i += 1
                continue
        if not s:
            i += 1
            continue
        if s.startswith("# "):
            title = s[2:]
            if title.startswith(("Модуль 1.", "Модуль 2.", "Модуль 3.", "Модуль 4.", "Модуль 5.", "Модуль 6.", "Модуль 7.", "Финал.", "Источники")):
                story.append(PageBreak())
            elif title != "Введение":
                story.append(Spacer(1, 18))
            kicker = Paragraph(
                '<font color="#075BFF"><b>DOORKICK / ПОЛНОЕ ИЗДАНИЕ</b></font>',
                ParagraphStyle("kicker", fontName="ArialBold", fontSize=8.5,
                               leading=13, spaceAfter=8, keepWithNext=1),
            )
            story.append(kicker)
            story.append(Paragraph(html.escape(title), styles["chapter"]))
            i += 1
            continue
        if s.startswith("### "):
            story.append(Paragraph(html.escape(s[4:]), styles["subhead"]))
            i += 1
            continue
        if s.startswith("## "):
            story.append(Paragraph(html.escape(s[3:]), styles["term"]))
            i += 1
            continue
        if s.startswith("[[diagram:"):
            kind = s.removeprefix("[[diagram:").removesuffix("]]")
            story.append(Spacer(1, 5))
            story.append(Diagram(kind))
            if kind != "next":
                story.append(Paragraph("СХЕМА / DoorKick. Векторная иллюстрация для чтения и печати.",
                                       styles["caption"]))
            i += 1
            continue
        if s.startswith("~~~"):
            lang = s[3:]
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("~~~"):
                code.append(lines[i])
                i += 1
            story.append(code_panel("\n".join(code), lang))
            story.append(Spacer(1, 11))
            i += 1
            continue
        if s.startswith(">"):
            story.append(Spacer(1, 4))
            story.append(quote_panel(s[1:].strip()))
            story.append(Spacer(1, 15))
            i += 1
            continue
        para_lines = []
        while i < len(lines):
            row = lines[i]
            if not row.strip() or row.startswith("#") or row.startswith("[[diagram:") or row.startswith("~~~") or row.startswith(">"):
                break
            para_lines.append(row.rstrip())
            i += 1
        raw = "\n".join(para_lines)
        if not raw:
            i += 1
            continue
        style = styles["meta"] if raw.startswith("**EN:**") or raw.startswith("**Просто:**") else styles["body"]
        story.append(KeepTogether([Paragraph(para_markup(raw), style)]))
    return story


def main():
    WORK.mkdir(exist_ok=True)
    doc = BookDoc(
        str(BODY_PDF), pagesize=A4,
        leftMargin=LEFT, rightMargin=RIGHT,
        topMargin=TOP, bottomMargin=BOTTOM,
        title="DoorKick — полная книга",
        author="DoorKick",
        subject="Самоучитель по IT, кибербезопасности и ИИ: модули 0–7 и финал Senior SecOps",
        pageCompression=1,
    )
    doc.multiBuild(build_story(), onFirstPage=page_decor, onLaterPages=page_decor)
    draw_cover()
    writer = PdfWriter()
    writer.append(str(COVER_PDF))
    writer.append(str(BODY_PDF))
    writer.add_metadata({
        "/Title": "DoorKick — полная книга",
        "/Author": "DoorKick",
        "/Subject": "Модули 0–5, 55 терминов и путь до Senior SecOps",
    })
    with FINAL_PDF.open("wb") as f:
        writer.write(f)
    reader = PdfReader(str(FINAL_PDF))
    print(f"PDF: {FINAL_PDF}")
    print(f"Pages: {len(reader.pages)}")
    print(f"Bytes: {FINAL_PDF.stat().st_size}")


if __name__ == "__main__":
    main()
