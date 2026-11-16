"""
scripts/remove_bg_hands.py

Menghapus latar belakang foto isyarat tangan lalu mengisinya dengan warna
#F8F2FF (warna latar kartu SignTalk).

Alur:
  1. Foto asli taruh di  static/img/hands_original/   (A.jpeg, B.jpeg, ...)
  2. Jalankan:           python scripts/remove_bg_hands.py
  3. Hasil otomatis ke   static/img/hands/            (dipakai oleh kartu)

Foto yang baru ditaruh langsung di static/img/hands/ otomatis dipindah dulu
ke hands_original/ sebagai cadangan sebelum diproses.
Opsi: python scripts/remove_bg_hands.py A B C   (hanya huruf tertentu)
"""

import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from rembg import new_session, remove

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "img" / "hands"
ORIG_DIR = ROOT / "static" / "img" / "hands_original"
EXTS = {".jpeg", ".jpg", ".png", ".webp"}
BACKGROUND = (0xF8, 0xF2, 0xFF)  # #F8F2FF


def keep_main_person(cutout, erode=14):
    """Buang orang/benda lain di belakang, simpan hanya orang utama.

    Mask dikikis dulu supaya orang di belakang yang menempel di bahu terputus,
    ambil gumpalan terbesar, lalu dikembangkan lagi (dibatasi mask asli).
    """
    alpha = np.array(cutout.split()[-1]).astype(np.float32)
    # Pertegas tepi: bayangan/sisa latar yang transparan sebagian dibuang
    alpha = np.clip((alpha - 110) / (200 - 110), 0, 1) * 255
    alpha = alpha.astype(np.uint8)
    solid = alpha > 128
    core = ndimage.binary_erosion(solid, iterations=erode)
    labels, count = ndimage.label(core)
    if count > 1:
        sizes = ndimage.sum(core, labels, range(1, count + 1))
        main_core = labels == (int(np.argmax(sizes)) + 1)
        keep = ndimage.binary_dilation(main_core, iterations=erode + 2) & (alpha > 20)
        alpha = np.where(keep, alpha, 0).astype(np.uint8)
    mask = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8))
    result = cutout.copy()
    result.putalpha(mask)
    return result


def main():
    only = {a.lower() for a in sys.argv[1:]}
    ORIG_DIR.mkdir(parents=True, exist_ok=True)

    # Cadangkan foto baru di folder hands/ yang belum punya salinan asli
    for f in OUT_DIR.iterdir():
        if f.suffix.lower() in EXTS and not (ORIG_DIR / f.name).exists():
            shutil.copy2(f, ORIG_DIR / f.name)

    files = sorted(p for p in ORIG_DIR.iterdir() if p.suffix.lower() in EXTS)
    if only:
        files = [p for p in files if p.stem.lower() in only]
    if not files:
        print("Tidak ada foto di", ORIG_DIR)
        return

    session = new_session("isnet-general-use")  # objek utama; orang di belakang ikut terbuang
    for src in files:
        image = Image.open(src).convert("RGB")
        cutout = keep_main_person(remove(image, session=session))
        canvas = Image.new("RGB", image.size, BACKGROUND)
        canvas.paste(cutout, mask=cutout.split()[-1])
        # Selalu simpan sebagai .jpeg; hapus versi lain agar tidak bentrok
        for other in OUT_DIR.glob(src.stem + ".*"):
            other.unlink()
        canvas.save(OUT_DIR / (src.stem + ".jpeg"), quality=92)
        print("[OK]", src.name)


if __name__ == "__main__":
    main()
