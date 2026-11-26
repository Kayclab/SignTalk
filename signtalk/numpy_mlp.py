"""
signtalk/numpy_mlp.py - Inference jaringan saraf (MLP) murni numpy.

Dipakai server ringan (Vercel) tanpa scikit-learn. Bobot diekspor dari
sklearn MLPClassifier (relu, softmax) lewat scripts/export_mlp_npz.py.
Hasil predict_proba sama dengan MLPClassifier.predict_proba.
"""

import numpy as np


class NumpyMLP:
    # Jaringan saraf lebih "yakin" daripada Random Forest (juga saat salah), sehingga
    # ambang keyakinan app perlu lebih tinggi: pada sesi uji independen, ambang 0,95
    # menampilkan lebih banyak jawaban benar dan lebih sedikit jawaban salah
    # dibanding Random Forest dengan ambang 0,55.
    confidence_threshold = 0.95

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.classes_ = z["classes"]
        self.n_features_in_ = int(z["n_features"])
        self._W = [z["W0"], z["W1"], z["W2"]]
        self._b = [z["b0"], z["b1"], z["b2"]]

    def predict_proba(self, X):
        h = np.asarray(X, dtype=np.float32).reshape(-1, self.n_features_in_)
        for W, b in zip(self._W[:-1], self._b[:-1]):
            h = np.maximum(h @ W + b, 0.0)          # relu
        logits = (h @ self._W[-1] + self._b[-1]).astype(np.float64)
        logits -= logits.max(axis=1, keepdims=True)  # softmax stabil
        e = np.exp(logits)
        return e / e.sum(axis=1, keepdims=True)

    def predict(self, X):
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]
