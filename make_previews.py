"""README with every reconstruction visible on the repository page.

GitHub does not autoplay videos inside a README, so each example becomes a small animated gif:
ground truth on the left, reconstruction on the right, playing in sync. README.md is written
from <dataset>/examples.tsv, so both stay consistent with the gallery.

Usage:  python make_previews.py      -> previews/<dataset>/<band>_<nn>.gif and README.md
"""
import csv
import html
from pathlib import Path

import av
import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
GALLERY = "https://fabriziospera.github.io/video_decoding_fMRI_reconstructions/"
DATASETS = [("cc2017", "CC2017"), ("bmd", "BOLD Moments")]
BANDS = [("best", "Best"), ("medium", "Medium"), ("worst", "Worst")]
TILE, GAP, HEAD, FPS, PER_ROW = 180, 4, 20, 8, 2
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def frames(path):
    """mp4 -> (frames (T, H, W, 3) uint8, duration in seconds)."""
    with av.open(str(path)) as c:
        v = np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)])
        return v, c.duration / 1e6


def at(video, duration, t):
    """Frame shown at time t of a clip lasting `duration` seconds."""
    return video[min(int(t / duration * len(video)), len(video) - 1)]


def pair_gif(gt_path, rec_path, dst, font):
    (gt, dg), (rc, dr) = frames(gt_path), frames(rec_path)
    W, H = 2 * TILE + GAP, HEAD + TILE
    out = []
    for k in range(int(round(dg * FPS))):
        t = (k + 0.5) / FPS
        canvas = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(canvas)
        d.text((TILE // 2, 2), "Ground truth", fill="black", font=font, anchor="mt")
        d.text((TILE + GAP + TILE // 2, 2), "Reconstruction", fill="black", font=font, anchor="mt")
        canvas.paste(Image.fromarray(at(gt, dg, t)).resize((TILE, TILE), Image.LANCZOS), (0, HEAD))
        canvas.paste(Image.fromarray(at(rc, dr, t)).resize((TILE, TILE), Image.LANCZOS), (TILE + GAP, HEAD))
        out.append(np.asarray(canvas))
    iio.imwrite(dst, np.stack(out), extension=".gif", duration=1000 / FPS, loop=0)


def main():
    font = ImageFont.truetype(FONT, 13)
    md = ["# fMRI-to-Video Reconstructions", "",
          f"### ▶ [Open the gallery as a web page]({GALLERY})", "",
          "Every reconstruction plays next to the clip the subject watched. For each dataset: 10 best,",
          "6 medium and 4 worst examples.", ""]
    for ds, ds_name in DATASETS:
        rows = list(csv.DictReader(open(HERE / ds / "examples.tsv"), delimiter="\t"))
        (HERE / "previews" / ds).mkdir(parents=True, exist_ok=True)
        md += [f"## {ds_name}", ""]
        for band, band_name in BANDS:
            items = [r for r in rows if r["band"] == band]
            md += [f"### {band_name}", "", "<table>"]
            for i in range(0, len(items), PER_ROW):
                md.append("<tr>")
                for r in items[i:i + PER_ROW]:
                    rel = f"previews/{ds}/{band}_{int(r['n']):02d}.gif"
                    pair_gif(HERE / ds / r["gt"], HERE / ds / r["recon"], HERE / rel, font)
                    stim = f"clip {r['stimulus']}" if ds == "cc2017" else r["stimulus"]
                    md.append(f'<td align="center"><img src="{rel}" width="{2 * TILE + GAP}"><br>'
                              f'<sub>Subject {r["subject"]} · {stim}<br><i>{html.escape(r["caption"].strip())}</i>'
                              f'</sub></td>')
                md.append("</tr>")
            md += ["</table>", ""]
        print(f"{ds}: {len(rows)} gifs")
    md += ["---", "",
           "`cc2017/` and `bmd/` hold the videos (`*_gt.mp4`, `*_recon.mp4`) grouped into `best/`, "
           "`medium/` and `worst/`. `index.html` is the gallery page (`python build_page.py` rebuilds it); "
           "`python make_previews.py` rebuilds the animations and this README.", ""]
    (HERE / "README.md").write_text("\n".join(md))
    print("written README.md")


if __name__ == "__main__":
    main()
