#!/usr/bin/env python3
import re, os, pathlib, shutil, subprocess, sys
from typing import Dict, Any, Tuple, List
import yaml  # PyYAML

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "third_party" / "esphome-docs" / "content"
OUTDIR = ROOT / "data"
OUT_MD = OUTDIR / "esphome-all.md"
OUT_PDF = OUTDIR / "esphome-all.pdf"

FRONT_RE = re.compile(r"(?s)^---\n.*?\n---\n")
ABS_LINK_RE = re.compile(r"\]\((/[^)]+)\)")   # ](/path) -> ](https://esphome.io/path)
IMG_SC_RE = re.compile(r"\{\{\<\s*img\s+([^>]+)\>\}\}")
ANCHOR_SC_RE = re.compile(r"\{\{\<\s*anchor\s+[^>]+?\>\}\}")
PR_SC_RE = re.compile(r"\{\{\<\s*pr\s+([^>]+)\>\}\}")

def parse_frontmatter(md: str) -> Tuple[Dict[str, Any], str]:
    m = FRONT_RE.match(md)
    if not m:
        return {}, md
    fm_text = m.group(0)[3:-4].strip()
    try:
        meta = yaml.safe_load(fm_text) or {}
        if not isinstance(meta, dict):
            meta = {}
    except Exception:
        meta = {}
    return meta, md[m.end():]

def demote_headings(md: str, delta: int = 1) -> str:
    def repl(m):
        hashes = m.group(1)
        return "#" * min(6, len(hashes) + delta) + " "
    return re.sub(r"(?m)^(#{1,6})\s", repl, md)

def fix_abs_links(md: str) -> str:
    return ABS_LINK_RE.sub(lambda m: f"](https://esphome.io{m.group(1)})", md)

def attrs_to_dict(attrs: str) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for m in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', attrs):
        d[m.group(1)] = m.group(2)
    return d

def replace_shortcodes(md: str) -> str:
    def img_repl(m):
        a = attrs_to_dict(m.group(1))
        src = a.get("src", "")
        alt = a.get("alt", "") or a.get("title", "")
        url = f"https://esphome.io{src}" if src.startswith("/") else src
        return f"![{alt}]({url})" if src else ""
    md = IMG_SC_RE.sub(img_repl, md)
    md = ANCHOR_SC_RE.sub("", md)
    def pr_repl(m):
        a = attrs_to_dict(m.group(1))
        num = a.get("number", "")
        repo = a.get("repo", "esphome")
        return f"(PR #{num} · {repo})" if num else ""
    md = PR_SC_RE.sub(pr_repl, md)
    return md

def dir_weights() -> Dict[pathlib.Path, int]:
    weights: Dict[pathlib.Path, int] = {}
    for p in SRC.rglob("_index.md"):
        meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        w = meta.get("weight")
        if isinstance(w, int):
            weights[p.parent] = w
    return weights

def collect() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    dweights = dir_weights()
    for p in SRC.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        meta, body = parse_frontmatter(text)
        items.append({
            "path": p,
            "dir_weight": dweights.get(p.parent, 10_000_000),
            "weight": meta.get("weight") if isinstance(meta.get("weight"), int) else 10_000_000,
            "title": meta.get("title", ""),
            "body": body,
        })
    items.sort(key=lambda x: (x["dir_weight"], x["weight"], str(x["path"]).lower()))
    return items

def write_markdown() -> int:
    if not SRC.exists():
        raise SystemExit(f"Missing source folder: {SRC}")
    OUTDIR.mkdir(parents=True, exist_ok=True)

    parts: List[str] = []
    header = (
        "# ESPHome — Documentation réunie en un seul fichier\n\n"
        "> **Source** : https://esphome.io/  \n"
        "> **Dépôt** : https://github.com/esphome/esphome-docs  \n"
        "> **Licence** : CC BY-NC-SA 4.0\n"
    )
    parts.append(header)

    count = 0
    for item in collect():
        rel = item["path"].relative_to(ROOT)
        md = item["body"]
        md = replace_shortcodes(md)
        md = fix_abs_links(md)
        md = demote_headings(md, delta=1)
        parts.append(f"\n\n---\n\n<!-- SOURCE: {rel} -->\n\n{md.strip()}\n")
        count += 1

    OUT_MD.write_text("\n".join(parts), encoding="utf-8")
    print(f"[OK] Wrote {OUT_MD} ({count} files)")
    return count

def run_pandoc(md_path: pathlib.Path, pdf_path: pathlib.Path) -> bool:
    """Essaie de générer un PDF avec Pandoc.
    Retourne True si succès, False sinon (sans interrompre le build)."""
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("[WARN] pandoc introuvable — PDF non généré. Installe pandoc + (TinyTeX ou wkhtmltopdf).", file=sys.stderr)
        return False

    # Arguments Pandoc simples. Si LaTeX n'est pas installé, on peut tenter wkhtmltopdf.
    args = [pandoc, str(md_path), "-o", str(pdf_path), "--from", "markdown+smart", "--toc"]
    # Essai 1 : moteur LaTeX par défaut
    try:
        subprocess.run(args, check=True)
        print(f"[OK] Wrote {pdf_path} (pandoc + LaTeX)")
        return True
    except subprocess.CalledProcessError:
        pass

    # Essai 2 : wkhtmltopdf si dispo
    if shutil.which("wkhtmltopdf"):
        try:
            args2 = args + ["--pdf-engine=wkhtmltopdf"]
            subprocess.run(args2, check=True)
            print(f"[OK] Wrote {pdf_path} (pandoc + wkhtmltopdf)")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERR] Echec pandoc avec wkhtmltopdf: {e}", file=sys.stderr)
            return False

    print("[ERR] pandoc trouvé mais échec de rendu PDF. Installe TinyTeX (LaTeX) ou wkhtmltopdf.", file=sys.stderr)
    return False

def main():
    count = write_markdown()

    # 1) Essayer Pandoc si présent (optionnel)
    ok = run_pandoc(OUT_MD, OUT_PDF)

    # 2) Sinon, fallback 100% Python (ReportLab + Mistune)
    if not ok:
        from md_to_pdf import md_to_pdf
        print("[INFO] Génération PDF en pur Python (ReportLab). Les images ne sont pas embarquées, rendu simple.")
        md_to_pdf(OUT_MD.read_text(encoding="utf-8"), str(OUT_PDF))
        print(f"[OK] Wrote {OUT_PDF} (pure Python)")


if __name__ == "__main__":
    main()
