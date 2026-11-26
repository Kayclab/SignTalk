"""
scripts/train_mlp_v8.py - Latih MLP V8 (jaringan saraf) dengan augmentasi kuat + cermin.

Hasil eksperimen (A=data lama, B=sesi uji lain yang tidak ikut latihan, C=rekaman baru):
  Random Forest lama : A 95,2%  B 62,2%  C 94,1%
  MLP V8             : A 96,5%  B 75,8%  C 96,1%

Pemakaian:  python scripts/train_mlp_v8.py          -> model/mlp_v8.pkl + model/mlp_v8.npz
"""
import sys, time, json, warnings, importlib.util
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

spec = importlib.util.spec_from_file_location('t7', 'scripts/train_model_v7.py')
t7 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t7)

X_all, y_all = t7.load(t7.DATASET_PATH)
Xold, yold = X_all[:t7.OLD_N], y_all[:t7.OLD_N]
Xnew, ynew = X_all[t7.OLD_N:], y_all[t7.OLD_N:]
Xte, yte = t7.load(t7.ROOT_DIR / 'dataset' / 'dataset_test_independent.csv')
tr_idx, va_idx = t7.blocked_split(yold)
H = 63


def strong_aug(X, rng, mirror_p=0.0):
    """Augmentasi kuat di ruang landmark: putar 3D, skala anisotropik, jitter, (opsional) cermin."""
    n = len(X)
    out = X.copy().reshape(n, 2, 21, 3).astype(np.float64)
    present = (np.abs(out).sum(axis=(2, 3)) > 1e-8)          # (n,2)
    ang = np.deg2rad(rng.uniform(-20, 20, (n, 2)))            # putar di bidang gambar
    ax = np.deg2rad(rng.uniform(-15, 15, (n, 2)))             # miring depan/belakang
    ay = np.deg2rad(rng.uniform(-15, 15, (n, 2)))             # miring kiri/kanan
    cz, sz = np.cos(ang), np.sin(ang)
    cx, sx_ = np.cos(ax), np.sin(ax)
    cy, sy_ = np.cos(ay), np.sin(ay)
    R = np.zeros((n, 2, 3, 3))
    # R = Rz @ Ry @ Rx
    Rx = np.stack([np.stack([np.ones_like(cx), np.zeros_like(cx), np.zeros_like(cx)], -1),
                   np.stack([np.zeros_like(cx), cx, -sx_], -1),
                   np.stack([np.zeros_like(cx), sx_, cx], -1)], -2)
    Ry = np.stack([np.stack([cy, np.zeros_like(cy), sy_], -1),
                   np.stack([np.zeros_like(cy), np.ones_like(cy), np.zeros_like(cy)], -1),
                   np.stack([-sy_, np.zeros_like(cy), cy], -1)], -2)
    Rz = np.stack([np.stack([cz, -sz, np.zeros_like(cz)], -1),
                   np.stack([sz, cz, np.zeros_like(cz)], -1),
                   np.stack([np.zeros_like(cz), np.zeros_like(cz), np.ones_like(cz)], -1)], -2)
    R = Rz @ Ry @ Rx
    out = np.einsum('nhij,nhpj->nhpi', R, out)
    scale = rng.uniform(0.9, 1.1, (n, 2, 1, 3))
    out *= scale
    out += rng.normal(0, 0.015, out.shape)
    mx = np.abs(out).reshape(n, 2, -1).max(axis=2).clip(min=1e-9)[:, :, None, None]
    out = out / mx                                             # normalisasi max-abs seperti fitur asli
    out[~present] = 0.0
    if mirror_p > 0:
        flip = rng.random(n) < mirror_p
        out[flip, :, :, 0] *= -1
        both = flip & present[:, 0] & present[:, 1]
        out[both] = out[both][:, ::-1]                         # tukar slot (urutan paling kiri dulu)
    return np.clip(out.reshape(n, 126), -1, 1).astype(np.float32)


def build(Xo, yo, Xt, yt, Xn, yn, rng, mode):
    Xb = np.vstack([Xo, Xt]); yb = np.concatenate([yo, yt])
    if mode == 'base':
        Xs = [Xb, t7.augment(Xb, rng)]; Nn = t7.NEW_AUG_COPIES
        newcopies = [Xn] + [t7.augment(Xn, rng) for _ in range(Nn)] if len(yn) else []
    else:
        mp = 0.5 if 'mirror' in mode else 0.0
        Xs = [Xb, strong_aug(Xb, rng, mp)]
        newcopies = ([Xn] + [strong_aug(Xn, rng, mp) for _ in range(3)]) if len(yn) else []
    ys = [yb, yb]; ws = [np.ones(len(yb))] * 2
    for c in newcopies:
        Xs.append(c); ys.append(yn); ws.append(np.full(len(yn), t7.NEW_WEIGHT))
    return np.vstack(Xs), np.concatenate(ys), np.concatenate(ws)


def make(model):
    if model == 'rf':
        return RandomForestClassifier(n_estimators=100, max_features='sqrt', class_weight='balanced_subsample', n_jobs=-1, random_state=42)
    if model == 'et':
        return ExtraTreesClassifier(n_estimators=100, max_features='sqrt', n_jobs=-1, random_state=42)
    if model == 'mlp':
        return MLPClassifier(hidden_layer_sizes=(256, 128), early_stopping=True, validation_fraction=0.05, n_iter_no_change=6,
                             max_iter=80, batch_size=256, random_state=42)


CONFIGS = {
    'base (RF, augmentasi kecil)': ('rf', 'base'),
    'RF + augmentasi kuat': ('rf', 'strong'),
    'RF + augmentasi kuat + cermin': ('rf', 'strong_mirror'),
    'ExtraTrees + augmentasi kuat + cermin': ('et', 'strong_mirror'),
    'MLP + augmentasi kuat + cermin': ('mlp', 'strong_mirror'),
}


def fit(model, X, y, w):
    m = make(model)
    if model == 'mlp':
        m.fit(X, y, sample_weight=w)
    else:
        m.fit(X, y, sample_weight=w)
    return m


def eval_A(model, mode):
    rng = np.random.default_rng(42)
    X, y, w = build(Xold[tr_idx], yold[tr_idx], Xte, yte, Xnew, ynew, rng, mode)
    m = fit(model, X, y, w)
    return float(accuracy_score(yold[va_idx], m.predict(Xold[va_idx])))


def eval_B(model, mode):
    rng = np.random.default_rng(42)
    X, y, w = build(Xold, yold, Xte[:0], yte[:0], Xnew, ynew, rng, mode)
    m = fit(model, X, y, w)
    return float(accuracy_score(yte, m.predict(Xte)))


def eval_C(model, mode, folds=3):
    blocks = t7.session_blocks(ynew)
    fold_of = np.zeros(len(ynew), dtype=int)
    for s, e in blocks:
        edges = np.linspace(s, e, folds + 1).astype(int)
        for f in range(folds):
            fold_of[edges[f]:edges[f + 1]] = f
    hit = tot = 0
    for f in range(folds):
        rng = np.random.default_rng(42 + f)
        m_tr, m_te = fold_of != f, fold_of == f
        X, y, w = build(Xold[tr_idx], yold[tr_idx], Xte, yte, Xnew[m_tr], ynew[m_tr], rng, mode)
        m = fit(model, X, y, w)
        p = m.predict(Xnew[m_te]); hit += int((p == ynew[m_te]).sum()); tot += int(m_te.sum())
    return hit / tot

import joblib

OUT_PKL = t7.MODEL_DIR / "mlp_v8.pkl"
OUT_NPZ = t7.MODEL_DIR / "mlp_v8.npz"

rng = np.random.default_rng(42)
X, y, w = build(Xold, yold, Xte, yte, Xnew, ynew, rng, "strong_mirror")
print("melatih MLP V8:", X.shape, flush=True)
m = make("mlp")
m.fit(X, y, sample_weight=w)
joblib.dump(m, OUT_PKL, compress=3)
np.savez_compressed(
    OUT_NPZ,
    classes=np.asarray(m.classes_).astype(str),
    n_features=np.int64(m.n_features_in_),
    W0=m.coefs_[0].astype(np.float32), b0=m.intercepts_[0].astype(np.float32),
    W1=m.coefs_[1].astype(np.float32), b1=m.intercepts_[1].astype(np.float32),
    W2=m.coefs_[2].astype(np.float32), b2=m.intercepts_[2].astype(np.float32),
)
print("disimpan:", OUT_PKL, OUT_NPZ, "| iterasi:", m.n_iter_, flush=True)
