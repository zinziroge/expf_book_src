"""第2章2.1節: 剰余項がなぜ「1つの項」で書けるのかを数値で確かめる。

テーラー展開をn次で打ち切ったときの誤差は、本来は打ち切った項の無限和である。

    R_n(x) = x^(n+1)/(n+1)! + x^(n+2)/(n+2)! + ...

ラグランジュの剰余項は、これが「たった1項」で書けると主張する。

    R_n(x) = exp(ξ)/(n+1)! * x^(n+1)      （ξ は 0 と x の間のどこか）

ここでは実際に R_n(x) を計算し、そこから ξ を逆算して、
本当に 0 と x の間に収まっているかを確かめる。

実行: ../py_tool/.venv/bin/python remainder_check.py
"""

from mpmath import mp, mpf, exp as mexp, log as mlog, factorial

mp.dps = 120


def taylor(x, n):
    s = mpf(0)
    for k in range(n + 1):
        s += mpf(x) ** k / factorial(k)
    return s


def rule(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


rule("[1] 打ち切り誤差は、切り捨てた最初の項とだいたい同じ大きさ")

print("R_n(x)   = 実際の打ち切り誤差 = exp(x) - Taylor_n(x)")
print("first    = 切り捨てた最初の項 = x^(n+1)/(n+1)!")
print()
print(f"{'x':>6} {'n':>3} | {'R_n(x)':>16} | {'first':>16} | {'R_n/first':>12}")
print("-" * 78)

cases = [(0.5, 3), (0.5, 5), (1.0, 3), (1.0, 5), (1.0, 10),
         (2.0, 5), (2.0, 10), (5.0, 10)]

for x, n in cases:
    ex = mexp(mpf(x))
    R = ex - taylor(x, n)
    first = mpf(x) ** (n + 1) / factorial(n + 1)
    print(f"{x:>6.1f} {n:>3} | {mp.nstr(R, 8):>16} | {mp.nstr(first, 8):>16} | "
          f"{mp.nstr(R / first, 6):>12}")

print()
print("R_n/first は 1 より少し大きい程度に収まっている。")
print("つまり「切り捨てた最初の項」が誤差のよい目安になる。")

rule("[2] その比は exp(ξ) であり、ξ は 0 と x の間に入っている")

print("R_n(x) = exp(ξ)/(n+1)! * x^(n+1) と置いて ξ を逆算する。")
print("  ξ = log( R_n(x) * (n+1)! / x^(n+1) ) = log( R_n / first )")
print()
print(f"{'x':>6} {'n':>3} | {'逆算した ξ':>16} | {'0 <= ξ <= x か':>16}")
print("-" * 78)

for x, n in cases:
    ex = mexp(mpf(x))
    R = ex - taylor(x, n)
    first = mpf(x) ** (n + 1) / factorial(n + 1)
    xi = mlog(R / first)
    ok = "OK" if mpf(0) <= xi <= mpf(x) else "NG"
    print(f"{x:>6.1f} {n:>3} | {mp.nstr(xi, 10):>16} | {ok:>16}")

print()
print("どの場合も ξ は 0 と x の間に入っている。")
print("「無限和が1項で書ける」のは、この ξ に無限和の情報を押し込めているから、")
print("と理解している。")

rule("[3] n=0 のときは平均値の定理そのものになる")

print("n=0 のとき、ラグランジュの剰余項は")
print("  exp(x) = 1 + exp(ξ) * x")
print("すなわち")
print("  (exp(x) - exp(0)) / (x - 0) = exp(ξ)")
print("これは「区間のどこかに、平均の傾きと同じ傾きの点がある」という")
print("平均値の定理の主張と同じ形をしている。")
print()
print(f"{'x':>6} | {'(exp(x)-1)/x':>16} | {'逆算した ξ':>16} | {'0 <= ξ <= x か':>16}")
print("-" * 78)
for x in [0.5, 1.0, 2.0, 5.0]:
    slope = (mexp(mpf(x)) - 1) / mpf(x)
    xi = mlog(slope)
    ok = "OK" if mpf(0) <= xi <= mpf(x) else "NG"
    print(f"{x:>6.1f} | {mp.nstr(slope, 10):>16} | {mp.nstr(xi, 10):>16} | {ok:>16}")

print()
print("ラグランジュの剰余項は、平均値の定理を高階へ拡張したものだと理解している。")
