"""Animated previews for the README: per dataset, a few examples with the ground truth above and
the reconstruction below, playing in sync.

Usage:  python make_previews.py      -> previews/cc2017.gif, previews/bmd.gif
"""
import csv
from pathlib import Path

import av
import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PICK = {"cc2017": [1, 2, 6, 8], "bmd": [3, 4, 9, 5]}          # rows of the "best" band
TILE, GAP, LABEL_W, FPS = 180, 6, 140, 8
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def frames(path):
    """mp4 -> (frames (T, H, W, 3) uint8, duration in seconds)."""
    with av.open(str(path)) as c:
        v = np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)])
        return v, c.duration / 1e6


def at(video, duration, t):
    """Frame shown at time t of a clip lasting `duration` seconds."""
    return video[min(int(t / duration * len(video)), len(video) - 1)]


def main():
    out = HERE / "previews"
    out.mkdir(exist_ok=True)
    font = ImageFont.truetype(FONT, 15)
    for ds, picks in PICK.items():
        rows = {int(r["n"]): r for r in csv.DictReader(open(HERE / ds / "examples.tsv"), delimiter="\t")
                if r["band"] == "best"}
        clips = [(frames(HERE / ds / rows[n]["gt"]), frames(HERE / ds / rows[n]["recon"])) for n in picks]
        duration = clips[0][0][1]
        n_out = int(round(duration * FPS))
        W = LABEL_W + len(clips) * (TILE + GAP)
        H = 2 * TILE + 3 * GAP
        out_frames = []
        for k in range(n_out):
            t = (k + 0.5) / FPS
            canvas = Image.new("RGB", (W, H), "white")
            d = ImageDraw.Draw(canvas)
            d.text((8, GAP + TILE // 2 - 9), "Ground truth", fill="black", font=font)
            d.text((8, 2 * GAP + TILE + TILE // 2 - 9), "Reconstruction", fill="black", font=font)
            for j, ((gt, dg), (rc, dr)) in enumerate(clips):
                x = LABEL_W + j * (TILE + GAP)
                canvas.paste(Image.fromarray(at(gt, dg, t)).resize((TILE, TILE), Image.LANCZOS), (x, GAP))
                canvas.paste(Image.fromarray(at(rc, dr, t)).resize((TILE, TILE), Image.LANCZOS), (x, 2 * GAP + TILE))
            out_frames.append(np.asarray(canvas))
        dst = out / f"{ds}.gif"
        iio.imwrite(dst, np.stack(out_frames), extension=".gif", duration=1000 / FPS, loop=0)
        print(f"written {dst} ({len(out_frames)} frames, {dst.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
