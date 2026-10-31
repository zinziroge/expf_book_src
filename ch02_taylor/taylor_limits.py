"""第2章「テーラー展開とその限界」で使う数値を実際に計算して出力する。

本文に載せる数値はすべてこのスクリプトの出力から取っている。
実行: ../py_tool/.venv/bin/python taylor_limits.py

「正解」はmpmathの高精度演算（10進200桁）で求めている。
"""

import struct

from mpmath import mp, mpf, exp as mexp, factorial

mp.dps = 200        # 10進200桁。float32(約7桁)に対しては十分すぎる精度

P = 24
HALF_ULP_REL = mpf(2) ** -24     # 正規化数での「0.5ulp相当」の相対誤差の目安


def f32(x) -> float:
    """最近接偶数丸めでfloat32に丸める。"""
    return struct.unpack("<f", struct.pack("<f", float(x)))[0]


def taylor(x, n: int):
    """exp(x)のマクローリン展開を第n次まで（項数n+1）高精度で計算する。"""
    x = mpf(x)
    s = mpf(0)
    for k in range(n + 1):
        s += x**k / factorial(k)
    return s


def rel_err(approx, exact) -> mpf:
    return abs((approx - exact) / exact)


def rule(title: str):
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


# --------------------------------------------------------------------------
rule("[1] 同じ次数でも、xが大きいほど誤差が大きい")

print("exp(x)を5次までのテーラー展開で近似したときの相対誤差")
print()
print(f"{'x':>8} | {'exact exp(x)':>22} | {'Taylor(5)':>22} | {'rel.err':>10}")
print("-" * 74)
for x in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
    ex = mexp(mpf(x))
    ap = taylor(x, 5)
    print(f"{x:>8.1f} | {mp.nstr(ex, 12):>22} | {mp.nstr(ap, 12):>22} | {mp.nstr(rel_err(ap, ex), 4):>10}")

# --------------------------------------------------------------------------
rule("[2] float32の精度(相対誤差 2^-24)に達するのに必要な次数")

print(f"目標: 相対誤差 < 2^-24 = {mp.nstr(HALF_ULP_REL, 6)}")
print()
print(f"{'x':>8} | {'必要な次数n':>12} | {'そのときの相対誤差':>20}")
print("-" * 74)
need = {}
for x in [0.125, 0.25, 0.3466, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 88.0]:
    ex = mexp(mpf(x))
    for n in range(0, 400):
        if rel_err(taylor(x, n), ex) < HALF_ULP_REL:
            need[x] = n
            print(f"{x:>8.4f} | {n:>12} | {mp.nstr(rel_err(taylor(x, n), ex), 6):>20}")
            break

print()
print("※ x=0.3466 は ln(2)/2 ≒ 0.34657 で、区間縮小後に扱う範囲の端に相当する。")
print("   （なぜこの値なのかは第6章の引数域縮小で扱う）")

# --------------------------------------------------------------------------
rule("[3] 区間内で誤差が均一でない（これがミニマックス近似の動機）")

n = 5
lo, hi = mpf(-1) / 2, mpf(1) / 2
print(f"次数{n}のテーラー展開を区間[-0.5, 0.5]で使ったときの相対誤差")
print()
print(f"{'x':>8} | {'rel.err':>14}")
print("-" * 74)
worst = mpf(0)
for i in range(-10, 11):
    x = lo + (hi - lo) * (i + 10) / 20
    e = rel_err(taylor(x, n), mexp(x))
    worst = max(worst, e)
    print(f"{float(x):>8.3f} | {mp.nstr(e, 6):>14}")
print()
print(f"区間内の最大相対誤差: {mp.nstr(worst, 6)}")
print("中心(x=0)では誤差ほぼ0、端で最大になる。")
print("→ 端の誤差を下げるために次数を上げると、中心では精度が無駄に余る。")

# --------------------------------------------------------------------------
rule("[4] 負の大きなxでは桁落ちで壊れる（float32で素直に足した場合）")

print("テーラー展開を float32 のまま素直に足し込むとどうなるか。")
print("x<0では項の符号が交互に変わり、途中の項が結果より遥かに大きくなる。")
print()
print(f"{'x':>8} | {'max|term|(f32)':>16} | {'f32 Taylor':>16} | {'exact':>16} | {'rel.err':>10}")
print("-" * 90)
for x in [-1.0, -5.0, -10.0, -20.0, -30.0]:
    # float32のまま、項を逐次計算して加算する
    s = f32(1.0)
    term = f32(1.0)
    maxterm = f32(1.0)
    for k in range(1, 200):
        term = f32(f32(term * f32(x)) / f32(k))
        s = f32(s + term)
        maxterm = max(maxterm, abs(term))
    ex = mexp(mpf(x))
    err = rel_err(mpf(s), ex) if s != 0 else mpf("inf")
    print(f"{x:>8.1f} | {maxterm:>16.6e} | {s:>16.6e} | {float(ex):>16.6e} | {mp.nstr(err, 4):>10}")

print()
print("x=-20あたりでは、途中の項が結果の10桁以上大きくなり、有効数字が残らない。")
print("→ exp(-x)=1/exp(x) と変形する、区間を狭める、といった対策が要る。")

# --------------------------------------------------------------------------
rule("[5] まとめ: 全区間を1つのテーラー展開で済ませようとするとどうなるか")

x = mpf(88)
ex = mexp(x)
print(f"x=88（float32でexpfが有限値を返すほぼ上限）で相対誤差2^-24を得るには")
print(f"  必要な次数: {need.get(88.0)}")
print(f"  そのとき最大の項 x^k/k! は約 {mp.nstr(max(x**k / factorial(k) for k in range(need.get(88.0) + 1)), 6)}")
print(f"  一方 exp(88) は約 {mp.nstr(ex, 6)}")
print("次数も、途中の項の大きさも現実的でない。区間縮小が必須になる。")
