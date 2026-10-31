"""第8章の図: 入力ごとのULP誤差を描く。

ulp_scan.c が書き出した ulp_bins.csv（区間ごとの最大ULP誤差）を読んで
グラフにする。

出力: ../figures/08-ulp/ulp-error.png（環境変数 EXPF_FIG_DIR で親ディレクトリを変更可）

実行: ../py_tool/.venv/bin/python plot_ulp.py

注意: 実行環境に日本語フォントが無いため、図中のラベルは英語にしている。
"""

import csv
import os
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
CSV = HERE / "ulp_bins.csv"
# 出力先の親ディレクトリは環境変数 EXPF_FIG_DIR で変えられる（既定はリポジトリ直下の figures/）
FIG_DIR = pathlib.Path(os.environ.get("EXPF_FIG_DIR", HERE.parent / "figures"))
OUT = FIG_DIR / "08-ulp" / "ulp-error.png"


def main():
    xs, e_expf, e_exp = [], [], []
    with CSV.open() as fp:
        for row in csv.DictReader(fp):
            xs.append(float(row["x"]))
            e_expf.append(float(row["expf_max_ulp"]))
            e_exp.append(float(row["exp_max_ulp"]))

    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(figsize=(6.6, 3.8))

    ax.plot(xs, e_expf, lw=1.0, label="expf(x)")
    ax.plot(xs, e_exp, lw=1.0, label="(float)exp((double)x)")
    ax.axhline(0.5, ls="--", lw=1.2, color="gray",
               label="0.5 ULP (correctly rounded limit)")

    ax.set_xlabel("x")
    ax.set_ylabel("max ULP error in bin")
    ax.set_title("Measured ULP error of expf (MPFR as reference)")
    ax.set_xlim(min(xs), max(xs))
    # 誤差はどれも0.5のごく近くに集まるので、その付近だけを拡大して見る
    lo = min(min(e_expf), min(e_exp))
    hi = max(max(e_expf), max(e_exp))
    margin = (hi - lo) * 0.25 or 0.001
    ax.set_ylim(lo - margin, hi + margin)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150)

    print(f"区間数            : {len(xs)}")
    print(f"expf の最大       : {max(e_expf):.4f} ULP")
    print(f"(float)exp の最大 : {max(e_exp):.4f} ULP")
    print(f"expf が0.5を超えた区間の数 : {sum(1 for v in e_expf if v > 0.5)} / {len(xs)}")
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()
