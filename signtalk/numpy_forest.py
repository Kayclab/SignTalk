"""
signtalk/numpy_forest.py - Random Forest inference murni numpy.

Dipakai di server ringan (Vercel) agar tidak perlu scikit-learn/scipy.
Model diekspor dari scikit-learn lewat scripts/export_forest_npz.py.
Hasil predict_proba identik dengan RandomForestClassifier.predict_proba.
"""

import numpy as np


class NumpyForest:
    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.classes_ = z["classes"]
        self.n_features_in_ = int(z["n_features"])
        self.roots = z["roots"].tolist()
        self.n_estimators = len(self.roots)
        # list Python lebih cepat daripada indexing scalar numpy untuk traversal
        self._left = z["left"].tolist()
        self._right = z["right"].tolist()
        self._feature = z["feature"].tolist()
        self._threshold = z["threshold"].tolist()
        self._value = z["value"]  # (total_node, n_kelas), float32, tiap baris jumlah 1

    def predict_proba(self, X):
        X = np.asarray(X, dtype=np.float32).reshape(-1, self.n_features_in_)
        left, right = self._left, self._right
        feature, threshold, value = self._feature, self._threshold, self._value
        out = np.zeros((X.shape[0], len(self.classes_)), dtype=np.float64)
        for i, row in enumerate(X):
            x = row.tolist()  # float32 -> float64 persis, sama seperti sklearn
            acc = np.zeros(len(self.classes_), dtype=np.float64)
            for node in self.roots:
                while True:
                    child = left[node]
                    if child < 0:
                        break
                    node = child if x[feature[node]] <= threshold[node] else right[node]
                acc += value[node]
            out[i] = acc / self.n_estimators
        return out

    def predict(self, X):
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]
