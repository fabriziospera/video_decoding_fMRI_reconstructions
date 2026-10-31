"""Build index.html (ground truth next to reconstruction) from cc2017/examples.tsv and bmd/examples.tsv.

Usage:  python build_page.py      -> rewrites index.html next to this file.
The data are embedded in the page, so it works both opened locally (file://) and on GitHub Pages.
"""
import csv, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASETS = [
    ("cc2017", "CC2017", "Wen et al. (2018) · 3 subjects · 2 s clips (6 frames at 3 fps)"),
    ("bmd", "BOLD Moments", "Lahner et al. (2024) · 10 subjects · 3 s clips"),
]
BANDS = [
    ("best", "Best", "Top reconstructions by the official metrics, content checked by eye."),
    ("medium", "Medium", "Around the median: scene type or layout right, details wrong."),
    ("worst", "Worst", "Bottom of the ranking: content not recovered."),
]

data = {}
for key, *_ in DATASETS:
    rows = list(csv.DictReader(open(HERE / key / "examples.tsv"), delimiter="\t"))
    data[key] = {b: [dict(subj=int(r["subject"]), stim=r["stimulus"], cap=r["caption"].strip(),
                          gt=f"{key}/{r['gt']}", rec=f"{key}/{r['recon']}")
                     for r in rows if r["band"] == b] for b, *_ in BANDS}

html = (HERE / "page_template.html").read_text()
html = html.replace("/*DATA*/", json.dumps(dict(data=data, datasets=DATASETS, bands=BANDS), ensure_ascii=False))
(HERE / "index.html").write_text(html)
print("written", HERE / "index.html")
