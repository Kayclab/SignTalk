
import pandas as pd
import numpy as np

df = pd.read_csv("dataset/dataset_tangan.csv")
X = df.iloc[:, 1:].to_numpy(dtype=float)

print("=" * 60)
print("1. PEMERIKSAAN KOORDINAT KELOMPOK 1")
print("=" * 60)

for i in [0, 740, 1000]:
    print(f"\nBaris {i} | Label: {df.iloc[i, 0]}")
    print("12 nilai pertama:")
    print(np.round(X[i, :12], 6))
    print("3 nilai pertama setiap landmark:")
    print(np.round(X[i, :63].reshape(21, 3)[:5], 6))

print("\n" + "=" * 60)
print("2. PEMERIKSAAN KOORDINAT KELOMPOK 2")
print("=" * 60)

for i in [0, 740, 1000]:
    print(f"\nBaris {i} | Label: {df.iloc[i, 0]}")
    print("12 nilai pertama:")
    print(np.round(X[i, 63:75], 6))
    print("3 nilai pertama setiap landmark:")
    print(np.round(X[i, 63:126].reshape(21, 3)[:5], 6))

print("\n" + "=" * 60)
print("3. RENTANG NILAI BERDASARKAN KOORDINAT")
print("=" * 60)

for start, end, name in [
    (0, 63, "Kelompok 1"),
    (63, 126, "Kelompok 2")
]:
    group = X[:, start:end].reshape(-1, 21, 3)

    print(f"\n{name}")
    for axis, axis_name in enumerate(["X", "Y", "Z"]):
        values = group[:, :, axis]
        nonzero = values[values != 0]

        if len(nonzero) > 0:
            print(
                f"{axis_name}: min={nonzero.min():.6f}, "
                f"max={nonzero.max():.6f}, "
                f"mean={nonzero.mean():.6f}"
            )

print("\nPemeriksaan koordinat selesai.")