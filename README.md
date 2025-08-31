# ESPHome Docs — One Big Markdown (MD + PDF)

Generate a **single Markdown file** (and a **PDF**) from the official ESPHome documentation (Hugo site). Useful for LLM/RAG ingestion or offline reading.

* **Live (LLM consumption)**: via GPT custom **ESPHome Pro Builder** → [https://chatgpt.com/g/g-68b3fa81e03c8191abfd6734a806702b-esphome-pro-builder](https://chatgpt.com/g/g-68b3fa81e03c8191abfd6734a806702b-esphome-pro-builder)
* **Outputs**:

  * `data/esphome-all.md` (concatenated doc, not fully clean, some Hugo tags still present)
  * `data/esphome-all.pdf` (via Pandoc if available, otherwise Python-only fallback)
* **File size**: < 5 MB in current version (manageable for most LLM contexts)

---

## Features

* Concatenates all `.md` files from `esphome-docs/content/` into one file.
* Cleans **front-matter**, processes some common **Hugo shortcodes** (`img`, `anchor`, `pr`) and makes links absolute.
* ⚠️ Many shortcodes and tags remain unprocessed → document is **not perfectly clean**, but sufficient for LLM ingestion.
* Demotes headings to avoid collisions.
* Sorts by Hugo `weight` then by path.
* **PDF**:

  * Attempt with **Pandoc** (higher quality, embedded images).
  * Fallback **Python-only** (ReportLab + Mistune) if Pandoc not found.

---

## Structure

```
esphome-docs-onefile/
├─ README.md
├─ LICENSE                 # license for YOUR scripts (e.g. MIT/Apache-2.0)
├─ NOTICE                  # credits/license for ESPHome docs (CC BY-NC-SA 4.0)
├─ .gitignore
├─ requirements.txt        # PyYAML, reportlab, mistune
├─ scripts/
│  └─ fetch_esphome_docs.sh
├─ src/
│  ├─ build_all_md.py      # build MD + PDF (Pandoc if available, else fallback)
│  └─ md_to_pdf.py         # Python-only PDF renderer (ReportLab + Mistune)
├─ third_party/
│  └─ esphome-docs/        # cloned by the script (or submodule)
└─ data/
   ├─ esphome-all.md
   └─ esphome-all.pdf
```

---

## Requirements

### Python

* **Python 3.10+** recommended.

### Python dependencies

Fallback PDF is Python-only, so install:

```
PyYAML>=6.0
reportlab>=4.0
mistune>=3.0
```

(see `requirements.txt`)

### (Optional) Pandoc

For higher-quality PDF (with images): install **Pandoc**

* Windows: `choco install pandoc -y` (admin) or MSI installer.
* macOS: `brew install pandoc`
* Linux (Debian/Ubuntu): `sudo apt-get install pandoc`

> **Optional** PDF engines: LaTeX (MiKTeX/TinyTeX/TeXLive) or `wkhtmltopdf`.

---

## Quickstart

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

./scripts/fetch_esphome_docs.sh
python .\src\build_all_md.py

ls .\data\esphome-all.*
```

### macOS / Linux (bash)

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

./scripts/fetch_esphome_docs.sh
python src/build_all_md.py

ls -lh data/esphome-all.*
```

**PDF behavior:**

* If **Pandoc** is available → `data/esphome-all.pdf` via Pandoc (higher quality, images).
* Else → **Python-only fallback** via `reportlab/mistune` (basic rendering, images shown as text).

---

## Main Script

* `src/build_all_md.py`

  * writes `data/esphome-all.md`
  * tries `pandoc` → `data/esphome-all.pdf`
  * if fails/missing, calls `src/md_to_pdf.py` (Python fallback)

---

## Known limitations

* Many Hugo shortcodes remain unprocessed → document not perfectly clean.
* **Fallback PDF** (ReportLab) does not embed images; they appear as `[Image: alt] (URL)` text.
* MD file is large but < 5 MB → chunk before LLM ingestion.

---

## LLM/RAG tips

* **Chunking** recommended (per page/section) before indexing.
* Keep **absolute links** for context verification.
* Preserve **license header** in any redistributed artifact.

---

## License & Credits

* **Build scripts**: MIT License © 2025 Yannick (see LICENSE).
* **ESPHome docs**: © ESPHome contributors, **CC BY-NC-SA 4.0**.

  * Attribution required; see `NOTICE` and header inserted in `esphome-all.md`.

---

## Troubleshooting

* **No PDF generated**: check Pandoc (`pandoc -v`). Otherwise, Python fallback should create PDF.
* **Encoding error**: force `UTF-8` in shell (`chcp 65001` on Windows).
* **Missing sources**: run `./scripts/fetch_esphome_docs.sh` before build.

---

## Contributing

PRs and issues welcome: improvements in shortcode parsing, new output formats (JSONL/TOC), and CI integration (GitHub Actions) to auto-publish artifacts (`data/`) on every tag.
