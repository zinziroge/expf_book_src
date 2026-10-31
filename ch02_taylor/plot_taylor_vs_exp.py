"""第2章の図: exp(x)とテーラー近似を重ね、xが大きくなるほど離れる様子を見せる。

出力: ../figures/02-taylor/taylor-vs-exp.png（環境変数 EXPF_FIG_DIR で親ディレクトリを変更可）

実行: ../py_tool/.venv/bin/python plot_taylor_vs_exp.py

注意: 実行環境に日本語フォントが無いため、図中のラベルは英語にしている。
注意: 白黒印刷を前提にしているため、色ではなく線種（点線・破線）と
      マーカーだけで系列を見分けられるようにしている。
"""

import os
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpmath import mp, mpf, exp as mexp, factorial

mp.dps = 60

DEGREES = [1, 2, 3, 5, 10]
X_LO, X_HI = 0.0, 8.0
# 出力先の親ディレクトリは環境変数 EXPF_FIG_DIR で変えられる（既定はリポジトリ直下の figures/）
FIG_DIR = pathlib.Path(os.environ.get("EXPF_FIG_DIR", pathlib.Path(__file__).resolve().parents[1] / "figures"))
OUT = FIG_DIR / "02-taylor" / "taylor-vs-exp.png"

# 白黒印刷でも区別できるよう、次数ごとに (線種, マーカー) を割り当てる。
# 線はすべて黒。マーカーは中抜きにして線が潰れないようにする。
STYLES = {
    1: ((0, (1, 2)), "o"),                    # 点線
    2: ((0, (4, 2)), "s"),                    # 破線
    3: ((0, (7, 2, 1, 2)), "^"),              # 一点鎖線
    5: ((0, (7, 2, 1, 2, 1, 2)), "D"),        # 二点鎖線
    10: ((0, ()), "v"),                       # 実線
}
# 正解カーブは太い灰色の帯にして、その上に黒い近似線を重ねる
EXACT_GRAY = "0.72"


def taylor(x, n):
    s = mpf(0)
    for k in range(n + 1):
        s += mpf(x) ** k / factorial(k)
    return s


def main():
    n = 401
    xs = [X_LO + (X_HI - X_LO) * i / (n - 1) for i in range(n)]
    exact = [mexp(mpf(x)) for x in xs]

    # 誌面では幅が限られるため、横並びではなく縦2段にする（縮小率を抑えて可読性を確保）
    plt.rcParams.update({"font.size": 11})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.4, 7.0))

    # 上: 関数そのものを重ねる
    ax1.plot(xs, [float(v) for v in exact], "-", color=EXACT_GRAY, lw=5.0,
             solid_capstyle="round", label="exp(x) (exact)", zorder=1)
    for i, d in enumerate(DEGREES):
        ls, mk = STYLES[d]
        ys = [float(taylor(x, d)) for x in xs]
        ax1.plot(xs, ys, color="black", lw=1.4, ls=ls,
                 marker=mk, markersize=5, markerfacecolor="white",
                 markeredgewidth=1.0, markevery=(8 * i, 50),
                 label=f"Taylor deg {d}", zorder=5)
    ax1.set_xlim(X_LO, X_HI)
    ax1.set_ylim(0, 3200)
    ax1.set_xlabel("x")
    ax1.set_ylabel("value")
    ax1.set_title("exp(x) and its Taylor approximations")
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9, loc="upper left")

    # 下: 相対誤差の伸び方
    for i, d in enumerate(DEGREES):
        ls, mk = STYLES[d]
        ys = [float(abs((taylor(x, d) - e) / e)) for x, e in zip(xs, exact)]
        ax2.semilogy(xs, ys, color="black", lw=1.4, ls=ls,
                     marker=mk, markersize=5, markerfacecolor="white",
                     markeredgewidth=1.0, markevery=(8 * i, 50),
                     label=f"Taylor deg {d}")
    ax2.axhline(2.0**-24, ls="-", lw=1.6, color=EXACT_GRAY, zorder=1,
                label="$2^{-24}$ (float32 half-ulp)")
    ax2.set_xlim(X_LO, X_HI)
    ax2.set_ylim(1e-18, 10)
    ax2.set_xlabel("x")
    ax2.set_ylabel("relative error")
    ax2.set_title("Relative error grows with x")
    ax2.grid(True, which="both", alpha=0.3)
    ax2.legend(fontsize=9, loc="lower right")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150)

    # 本文に書く数値も出しておく
    print("次数ごとに、相対誤差が2^-24を超えるxはどこか（実測）")
    print(f"{'degree':>8} | {'x where rel.err exceeds 2^-24':>32}")
    print("-" * 46)
    for d in DEGREES:
        thresh = None
        for x in xs:
            e = mexp(mpf(x))
            if abs((taylor(x, d) - e) / e) > mpf(2) ** -24:
                thresh = x
                break
        print(f"{d:>8} | {thresh if thresh is not None else '(範囲内では超えず)':>32}")

    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
