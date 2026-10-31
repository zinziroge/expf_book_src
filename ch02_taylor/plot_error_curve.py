"""第2章の図: テーラー展開とミニマックス近似の誤差カーブを比較する。

sollyaを呼んでミニマックス係数を求め、mpmathで誤差を評価して描画する。
出力: ../figures/02-taylor/error-curve.png（環境変数 EXPF_FIG_DIR で親ディレクトリを変更可）

実行: ../py_tool/.venv/bin/python plot_error_curve.py

注意: 実行環境に日本語フォントが無いため、図中のラベルは英語にしている。
注意: 白黒印刷を前提にしているため、色ではなく線種（実線・破線）と
      マーカーだけで系列を見分けられるようにしている。
"""

import os
import pathlib
import subprocess
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpmath import mp, mpf, exp as mexp, factorial

mp.dps = 120

DEG = 5
LO, HI = mpf(-1) / 2, mpf(1) / 2
# 出力先の親ディレクトリは環境変数 EXPF_FIG_DIR で変えられる（既定はリポジトリ直下の figures/）
FIG_DIR = pathlib.Path(os.environ.get("EXPF_FIG_DIR", pathlib.Path(__file__).resolve().parents[1] / "figures"))
OUT = FIG_DIR / "02-taylor" / "error-curve.png"

SOLLYA = """
prec = 200!;
display = decimal!;
f = exp(x);
d = [-0.5; 0.5];
p = remez(1, [|0,...,{deg}|], d, 1/f);
for i from 0 to {deg} do {{ write(coeff(p,i), "\\n"); }};
quit;
"""


def minimax_coeffs(deg: int):
    """sollyaで相対誤差ミニマックスの係数を求める。

    sollyaのremez(f,n,d,w)は ||f - p*w|| を最小化する。
    相対誤差 ||(f-p)/f|| = ||1 - p*(1/f)|| を最小化したいので、
    近似対象を1、重みを1/f とする。
    """
    with tempfile.NamedTemporaryFile("w", suffix=".sollya", delete=False) as fp:
        fp.write(SOLLYA.format(deg=deg))
        path = fp.name
    out = subprocess.run(["sollya", path], capture_output=True, text=True).stdout
    coeffs = [mpf(line.strip()) for line in out.splitlines() if line.strip()]
    assert len(coeffs) == deg + 1, f"想定外のsollya出力: {out!r}"
    return coeffs


def poly(coeffs, x):
    s = mpf(0)
    for c in reversed(coeffs):
        s = s * x + c
    return s


def taylor_coeffs(deg: int):
    return [1 / factorial(k) for k in range(deg + 1)]


def main():
    tc = taylor_coeffs(DEG)
    mc = minimax_coeffs(DEG)

    print(f"{'i':>3} | {'taylor a_i':>26} | {'minimax a_i':>26}")
    print("-" * 62)
    for i, (a, b) in enumerate(zip(tc, mc)):
        print(f"{i:>3} | {mp.nstr(a, 18):>26} | {mp.nstr(b, 18):>26}")

    n = 601
    xs, et, em = [], [], []
    for i in range(n):
        x = LO + (HI - LO) * i / (n - 1)
        ex = mexp(x)
        xs.append(float(x))
        et.append(float(abs((poly(tc, x) - ex) / ex)))
        em.append(float(abs((poly(mc, x) - ex) / ex)))

    print()
    print(f"taylor  max rel err = {max(et):.6e}")
    print(f"minimax max rel err = {max(em):.6e}")
    print(f"ratio               = {max(et) / max(em):.1f} 倍")

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    # 白黒印刷でも見分けられるよう、色ではなく線種とマーカーで区別する
    ax.semilogy(xs, et, color="black", lw=1.6, ls=(0, (5, 2)),
                marker="s", markersize=5, markerfacecolor="white",
                markeredgewidth=1.0, markevery=(0, 60),
                label=f"Taylor (degree {DEG})")
    ax.semilogy(xs, em, color="black", lw=1.6, ls="-",
                marker="o", markersize=5, markerfacecolor="white",
                markeredgewidth=1.0, markevery=(30, 60),
                label=f"Minimax (degree {DEG})")
    ax.axhline(2.0**-24, ls="-", lw=1.8, color="0.72", zorder=1,
               label="$2^{-24}$ (float32 half-ulp)")
    ax.set_xlabel("x")
    ax.set_ylabel("relative error")
    ax.set_title(f"exp(x) on [-0.5, 0.5]: Taylor vs Minimax (same degree {DEG})")
    ax.set_ylim(1e-12, 1e-3)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150)
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
