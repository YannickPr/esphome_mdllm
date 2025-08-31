# src/md_to_pdf.py
# Rendu Markdown -> PDF en "pur Python" (ReportLab + Mistune)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem, Preformatted, HRFlowable
from reportlab.pdfbase.pdfmetrics import stringWidth
import mistune

def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="H1", parent=ss["Heading1"], spaceBefore=12, spaceAfter=6))
    ss.add(ParagraphStyle(name="H2", parent=ss["Heading2"], spaceBefore=12, spaceAfter=6))
    ss.add(ParagraphStyle(name="H3", parent=ss["Heading3"], spaceBefore=10, spaceAfter=4))
    # Customize the existing 'Code' style
    code_style = ss["Code"]
    code_style.fontName = "Courier"
    code_style.fontSize = 9
    code_style.leading = 11
    code_style.leftIndent = 6
    code_style.rightIndent = 6
    code_style.backColor = None
    code_style.spaceBefore = 6
    code_style.spaceAfter = 6
    ss.add(ParagraphStyle(name="Body", parent=ss["BodyText"], spaceAfter=6))
    return ss

def md_to_pdf(md_text: str, out_pdf_path: str):
    """Rendu minimaliste et robuste. Images ignorées; liens rendus en texte."""
    ss = _styles()
    doc = SimpleDocTemplate(out_pdf_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    flow = []

    # Mistune en mode tokens (AST)
    markdown = mistune.Markdown()
    ast = markdown.parse(md_text)[0]

    def para(text):
        flow.append(Paragraph(text, ss["Body"]))

    def heading(text, level):
        name = {1:"H1",2:"H2",3:"H3"}.get(level, "H3")
        flow.append(Paragraph(text, ss[name]))

    def bullet_list(items, ordered=False):
        lst = []
        for it in items:
            lst.append(ListItem(Paragraph(it, ss["Body"])))
        flow.append(ListFlowable(lst, bulletType='1' if ordered else 'bullet', start='1'))

    def codeblock(code):
        flow.append(Preformatted(code, ss["Code"]))

    def hr():
        flow.append(Spacer(1, 6))
        flow.append(HRFlowable(width="100%", thickness=0.5))
        flow.append(Spacer(1, 6))

    # Très petit interpréteur d’AST
    def inline(children):
        # Transforme les inlines en texte "reportlab-friendly" avec un peu de HTML <b>/<i>/<u>/<a>
        out = ""
        for node in children:
            t = node["type"]
            if t == "text":
                out += node["raw"]
            elif t == "linebreak":
                out += "<br/>"
            elif t == "softbreak":
                out += " "
            elif t == "emphasis":
                out += f"<i>{inline(node['children'])}</i>"
            elif t == "strong":
                out += f"<b>{inline(node['children'])}</b>"
            elif t == "link":
                label = inline(node["children"])
                href = node["attrs"]["url"]
                out += f"{label} ({href})" if href else label
            elif t == "codespan":
                out += f"<font face='Courier'>{node['raw']}</font>"
            elif t == "image":
                alt = node["attrs"].get("alt","")
                src = node["attrs"]["url"]
                out += f"[Image: {alt}] ({src})"
            else:
                # fallback
                if "children" in node:
                    out += inline(node["children"])
        return out

    i = 0
    while i < len(ast):
        node = ast[i]
        t = node["type"]

        if t == "heading":
            heading(inline(node["children"]), node["attrs"]["level"])
        elif t == "paragraph":
            para(inline(node["children"]))
        elif t == "block_quote":
            # Rendu simple: indentation via paragraphe
            txt = inline(node["children"][0]["children"]) if node.get("children") else ""
            flow.append(Paragraph(f"&ldquo;{txt}&rdquo;", ss["Body"]))
        elif t == "list":
            items = []
            for li in node["children"]:
                # chaque item est un paragraphe/ensemble
                chunks = []
                for c in li.get("children", []):
                    if c["type"] == "paragraph":
                        chunks.append(inline(c["children"]))
                    elif c["type"] == "text":
                        chunks.append(c["text"])
                items.append(" ".join(chunks))
            bullet_list(items, ordered=node["attrs"].get("ordered", False))
        elif t == "thematic_break":
            hr()
        elif t == "code":
            codeblock(node["text"])
        elif t == "table":
            # Pour rester léger: rend la table en texte simple
            header = [" | ".join([inline(cell["children"]) for cell in node["children"][0]["children"]])]
            rows = [" | ".join([inline(cell["children"]) for cell in row["children"]]) for row in node["children"][1:]]
            para("\n".join(header + ["—"*20] + rows))
        else:
            # Fallback: si on a un contenu inline
            if "children" in node:
                para(inline(node["children"]))
        i += 1

    doc.build(flow)
