"""
SIGNTALK - RANDOM FOREST V6/V7 (tag diatur lewat TAG)
Menambahkan rekaman baru (tangan kiri/kanan, terang/gelap) ke resep V4.
Tidak menimpa V4.

Sumber latih:
  1. dataset/dataset_v2.csv  baris 0..OLD_N-1      (data lama, split blok 80/20 seperti V4)
  2. dataset/dataset_test_independent.csv          (seperti V4)
  3. dataset/dataset_v2.csv  baris OLD_N..akhir    (REKAMAN BARU, diberi bobot lebih besar)

Pemakaian:
  python scripts/train_model_v6.py --cv      validasi silang pada rekaman baru (per sesi, blok berurutan)
  python scripts/train_model_v6.py --final   latih memakai SEMUA data dan simpan model V6
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from signtalk.features import FEATURE_COLUMNS, FEATURE_VERSION, HAND_FEATURES  # noqa: E402
from signtalk.paths import DATASET_PATH, MODEL_DIR  # noqa: E402

OLD_N = 40417            # jumlah baris dataset_v2.csv SEBELUM rekaman baru
NEW_WEIGHT = 4.0         # bobot sampel rekaman baru
NEW_AUG_COPIES = 3       # salinan augmentasi tiap sampel baru
N_FOLDS = 5
SEED = 42
JITTER_STD = 0.008
ROTATION_MAX = 0.035
GAP_ROWS = 10
VAL_FRACTION = 0.20

TAG = "v7"
OUT_MODEL = MODEL_DIR / f"random_forest_{TAG}.pkl"
OUT_META = MODEL_DIR / f"model_{TAG}_meta.json"


def load(path):
    df = pd.read_csv(path)
    X = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="raise").to_numpy(np.float32)
    y = df["label"].astype(str).str.strip().to_numpy()
    return X, y


def blocked_split(y):
    """Sama seperti V4: 20% terakhir tiap kelas = validasi, dengan jeda GAP_ROWS."""
    tr, va = [], []
    for label in np.unique(y):
        idx = np.flatnonzero(y == label)
        n = len(idx)
        if n < 10:
            tr.extend(idx.tolist())
            continue
        vc = max(1, int(round(n * VAL_FRACTION)))
        sp = n - vc
        tr.extend(idx[:max(1, sp - GAP_ROWS)].tolist())
        va.extend(idx[sp:].tolist())
    return np.array(sorted(tr)), np.array(sorted(va))


def augment(X, rng):
    out = X.copy()
    for i in range(len(out)):
        for slot in range(2):
            s, e = slot * HAND_FEATURES, (slot + 1) * HAND_FEATURES
            hand = out[i, s:e]
            if np.abs(hand).sum() < 1e-8:
                continue
            hand = hand.reshape(21, 3).copy()
            a = rng.uniform(-ROTATION_MAX, ROTATION_MAX)
            c, sn = np.cos(a), np.sin(a)
            x, yv = hand[:, 0].copy(), hand[:, 1].copy()
            hand[:, 0] = x * c - yv * sn
            hand[:, 1] = x * sn + yv * c
            hand += rng.normal(0, JITTER_STD, size=hand.shape).astype(np.float32)
            out[i, s:e] = hand.flatten()
    return np.clip(out, -1, 1)


def session_blocks(y):
    """Sesi rekam = deretan label sama yang berurutan."""
    blocks, s = [], 0
    for i in range(1, len(y) + 1):
        if i == len(y) or y[i] != y[s]:
            blocks.append((s, i))
            s = i
    return blocks


def build_train(Xold, yold, Xte, yte, Xnew, ynew, rng):
    """Data latih + bobot: lama/uji (x1 augmentasi, bobot 1), baru (xN augmentasi, bobot NEW_WEIGHT)."""
    Xb = np.vstack([Xold, Xte])
    yb = np.concatenate([yold, yte])
    Xs = [Xb, augment(Xb, rng)]
    ys = [yb, yb]
    ws = [np.ones(len(yb)), np.ones(len(yb))]
    if len(ynew):
        for k in range(NEW_AUG_COPIES + 1):
            Xs.append(Xnew if k == 0 else augment(Xnew, rng))
            ys.append(ynew)
            ws.append(np.full(len(ynew), NEW_WEIGHT))
    return np.vstack(Xs), np.concatenate(ys), np.concatenate(ws)


def make_rf(n):
    return RandomForestClassifier(
        n_estimators=n, max_features="sqrt", min_samples_leaf=1,
        class_weight="balanced_subsample", n_jobs=-1, random_state=SEED,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", action="store_true")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--trees", type=int, default=0)
    args = ap.parse_args()
    if not (args.cv or args.final):
        ap.error("pilih --cv atau --final")

    X_all, y_all = load(DATASET_PATH)
    Xold, yold = X_all[:OLD_N], y_all[:OLD_N]
    Xnew, ynew = X_all[OLD_N:], y_all[OLD_N:]
    Xte, yte = load(ROOT_DIR / "dataset" / "dataset_test_independent.csv")
    print(f"data lama {len(yold):,} | uji {len(yte):,} | baru {len(ynew):,} "
          f"({', '.join(f'{k}={int((ynew == k).sum())}' for k in np.unique(ynew))})")

    rng = np.random.default_rng(SEED)
    tr_idx, va_idx = blocked_split(yold)

    if args.cv:
        blocks = session_blocks(ynew)
        fold_of = np.zeros(len(ynew), dtype=int)
        for s, e in blocks:
            edges = np.linspace(s, e, N_FOLDS + 1).astype(int)
            for f in range(N_FOLDS):
                fold_of[edges[f]:edges[f + 1]] = f
        trees = args.trees or 150
        hits, tot = {}, {}
        old_hits = 0
        confusions = {}
        for f in range(N_FOLDS):
            m_tr, m_te = fold_of != f, fold_of == f
            X, y, w = build_train(Xold[tr_idx], yold[tr_idx], Xte, yte, Xnew[m_tr], ynew[m_tr], rng)
            rf = make_rf(trees)
            rf.fit(X, y, sample_weight=w)
            p = rf.predict(Xnew[m_te])
            for k in np.unique(ynew):
                mk = ynew[m_te] == k
                hits[k] = hits.get(k, 0) + int((p[mk] == k).sum())
                tot[k] = tot.get(k, 0) + int(mk.sum())
                for pred in p[mk]:
                    if pred != k:
                        confusions.setdefault(k, {}).setdefault(pred, 0)
                        confusions[k][pred] += 1
            pv = rf.predict(Xold[va_idx])
            acc_old = float((pv == yold[va_idx]).mean())
            old_hits += acc_old
            print(f"  fold {f + 1}/{N_FOLDS}: data lama (validasi V4) akurasi {acc_old:.4f}", flush=True)
        print("\nVALIDASI SILANG pada rekaman baru (tiap fold = bagian waktu yang BELUM dilihat model):")
        for k in sorted(hits):
            top = sorted(confusions.get(k, {}).items(), key=lambda t: -t[1])[:3]
            print(f"  {k:15s} benar {hits[k] / tot[k]:.2f}  ({hits[k]}/{tot[k]})  salah jadi: {top}")
        allh, allt = sum(hits.values()), sum(tot.values())
        print(f"  TOTAL rekaman baru: {allh / allt:.3f}   (model lama V4: 0.477)")
        print(f"  Data lama (validasi V4), rata-rata: {old_hits / N_FOLDS:.4f}   (model lama V4: 0.9228)")
        return

    # --final
    X, y, w = build_train(Xold, yold, Xte, yte, Xnew, ynew, rng)
    trees = args.trees or 300
    print(f"melatih {TAG.upper()}: {len(y):,} baris, {trees} pohon ...", flush=True)
    rf = make_rf(trees)
    rf.fit(X, y, sample_weight=w)
    joblib.dump(rf, OUT_MODEL, compress=3)
    OUT_META.write_text(json.dumps({
        "model_name": f"Random Forest {TAG.upper()}",
        "feature_version": FEATURE_VERSION,
        "n_features": len(FEATURE_COLUMNS),
        "classes": [str(c) for c in rf.classes_],
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "new_data_rows": int(len(ynew)),
        "new_data_weight": NEW_WEIGHT,
    }, indent=4), encoding="utf-8")
    print("disimpan:", OUT_MODEL, f"({OUT_MODEL.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
