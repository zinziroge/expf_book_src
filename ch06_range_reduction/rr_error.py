"""第6章: 引数域縮小そのものが持ち込む誤差を見積もる。

多項式近似の誤差とは別に、z = InvLn2N * x を double で計算する時点で
すでに誤差が入っている。その大きさを調べる。

  z_true = x * (N / ln2)          … 数学的に正しい値
  z      = fl(InvLn2N * x)        … 実際に計算される値

z がずれると、最終結果 2^(z/N) もずれる。
相対誤差はおよそ |z - z_true| * ln2 / N になる。

実行: ../py_tool/.venv/bin/python rr_error.py
"""

import random
import struct

from mpmath import mp, mpf, log as mlog

mp.prec = 300

N = 32
INVLN2N = float.fromhex("0x1.71547652b82fep+0") * N   # ソース上の定数


def f32(x) -> float:
    return struct.unpack("<f", struct.pack("<f", float(x)))[0]


def rule(t):
    print()
    print("=" * 74)
    print(t)
    print("=" * 74)


ln2 = mlog(2)
true_invln2n = N / ln2

# --------------------------------------------------------------------------
rule("[1] 定数 InvLn2N 自体のずれ")

d1 = (mpf(INVLN2N) - true_invln2n) / true_invln2n
print(f"厳密な N/ln2          = {mp.nstr(true_invln2n, 22)}")
print(f"ソース上の InvLn2N    = {mp.nstr(mpf(INVLN2N), 22)}")
print(f"相対誤差              = {mp.nstr(d1, 6)}")
print(f"                      = {mp.nstr(abs(d1) / mpf(2)**-53, 4)} × 2^-53")
print()
print("0x1.71547652b82fep+0 は 1/ln2 に最も近い double。")
print("それを32倍（2の冪なので誤差なし）したものが InvLn2N。")

# --------------------------------------------------------------------------
rule("[2] 実際の入力での z のずれ")

# 端と、ランダムな入力を混ぜて調べる
random.seed(1)
xs = [-103.97, -87.3, -50.0, -10.0, -1.0, -0.1,
      0.1, 1.0, 10.0, 50.0, 87.0, 88.72]
xs += [random.uniform(-103.9, 88.7) for _ in range(2000)]

worst_dz = mpf(0)
worst_x = None
worst_rel = mpf(0)

for xv in xs:
    x = f32(xv)
    if x == 0:
        continue
    z = INVLN2N * x                      # doubleでの計算（Pythonのfloatはdouble）
    z_true = mpf(x) * true_invln2n
    dz = abs(mpf(z) - z_true)
    # z のずれが最終結果に与える相対誤差
    rel = dz * ln2 / N
    if rel > worst_rel:
        worst_rel, worst_dz, worst_x = rel, dz, x

print(f"調べた入力の数: {len(xs)}")
print()
print(f"最悪だった入力 x   = {worst_x!r}")
print(f"  |z - z_true|     = {mp.nstr(worst_dz, 6)}")
print(f"  最終結果への相対誤差 ≈ {mp.nstr(worst_rel, 6)}")
print(f"                     = {mp.nstr(worst_rel / mpf(2)**-24, 6)} × 2^-24")
print(f"                     = {mp.nstr(worst_rel / mpf(2)**-24, 4)} ulp 相当")

# --------------------------------------------------------------------------
rule("[3] 多項式近似の誤差と比べる")

poly_err = mpf("1.69") * mpf(2) ** -34
print(f"多項式近似の誤差（ソースのコメント） = 1.69 * 2^-34")
print(f"                                    = {mp.nstr(poly_err, 6)}")
print(f"引数域縮小の誤差（上で測った最悪値） = {mp.nstr(worst_rel, 6)}")
print()
if worst_rel < poly_err:
    print(f"引数域縮小の誤差のほうが {mp.nstr(poly_err / worst_rel, 4)} 倍小さい。")
    print("誤差の主役は多項式近似のほうだと言える。")
else:
    print(f"引数域縮小の誤差のほうが {mp.nstr(worst_rel / poly_err, 4)} 倍大きい。")

print()
print("参考: float32で最終的に許される誤差")
print(f"  0.5 ulp 相当の相対誤差 = 2^-24 = {mp.nstr(mpf(2)**-24, 6)}")
