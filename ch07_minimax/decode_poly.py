"""第7章: glibcの多項式係数が何を近似しているのかを突き止める。

e_expf.c の多項式評価はこうなっている（C = poly_scaled）。

    z = C[0] * r + C[1];
    r2 = r * r;
    y = C[2] * r + 1;
    y = z * r2 + y;
      = C[0]*r^3 + C[1]*r^2 + C[2]*r + 1

e_exp2f_data.c を見ると poly_scaled は poly を N の冪で割ったものである。

    poly_scaled = { poly[0]/N/N/N, poly[1]/N/N, poly[2]/N }

これを代入すると t = r/N の多項式になるはず、という仮説を確かめる。

実行: ../py_tool/.venv/bin/python decode_poly.py
"""

from mpmath import mp, mpf, log as mlog, factorial

mp.dps = 60

N = 32

# e_exp2f_data.c の .poly
POLY = [
    mpf(float.fromhex("0x1.c6af84b912394p-5")),   # 3次の係数
    mpf(float.fromhex("0x1.ebfce50fac4f3p-3")),   # 2次の係数
    mpf(float.fromhex("0x1.62e42ff0c52d6p-1")),   # 1次の係数
]

HALF = mpf(1) / (2 * N)      # t の範囲の半幅 = 1/64


def rule(t):
    print()
    print("=" * 74)
    print(t)
    print("=" * 74)


def p_of_t(t):
    """1 + poly[2]*t + poly[1]*t^2 + poly[0]*t^3"""
    return 1 + POLY[2] * t + POLY[1] * t**2 + POLY[0] * t**3


def max_rel_err(f, g, lo, hi, n=20001):
    """区間[lo,hi]をn点で刻んで |f/g - 1| の最大値を求める。"""
    worst = mpf(0)
    worst_t = lo
    for i in range(n):
        t = lo + (hi - lo) * i / (n - 1)
        e = abs(f(t) / g(t) - 1)
        if e > worst:
            worst, worst_t = e, t
    return worst, worst_t


# --------------------------------------------------------------------------
rule("[1] 仮説: poly は 2^t を t in [-1/64, 1/64] で近似している")

err, at = max_rel_err(p_of_t, lambda t: mpf(2) ** t, -HALF, HALF)
target = mpf("1.69") * mpf(2) ** -34

print(f"t の範囲       : ±{mp.nstr(HALF, 8)} (= ±1/{2*N})")
print(f"最大相対誤差   : {mp.nstr(err, 8)}   (t = {mp.nstr(at, 6)})")
print(f"                 = {mp.nstr(err / mpf(2)**-34, 6)} × 2^-34")
print()
print(f"ソースのコメント: 1.69 * 2^-34 = {mp.nstr(target, 8)}")
print()
if abs(err / target - 1) < mpf("0.05"):
    print("-> コメントの値と一致した。仮説は正しい。")
else:
    print("-> 一致しない。仮説が違うか、別の解釈が要る。")

# --------------------------------------------------------------------------
rule("[2] 念のため: 別の解釈だと合わないことを確認する")

# 仮説が外れていた場合に備え、r をそのまま使う解釈も試す（|r| <= 1/2）
err2, _ = max_rel_err(p_of_t, lambda t: mpf(2) ** t, mpf(-1) / 2, mpf(1) / 2)
print(f"もし t の範囲が ±1/2 だとした場合の最大相対誤差: {mp.nstr(err2, 6)}")
print(f"  -> 2^-34 = {mp.nstr(mpf(2)**-34, 6)} と比べて桁違いに大きい")
print("  つまり N で割ったスケーリングの解釈が正しい。")

# --------------------------------------------------------------------------
rule("[3] 係数はテーラー展開とどれくらい違うのか")

# 2^t のマクローリン展開: 2^t = sum (ln2)^k t^k / k!
ln2 = mlog(2)
taylor_coeffs = [ln2**k / factorial(k) for k in range(4)]

print("2^t のテーラー展開の係数は (ln2)^k / k! である。")
print()
print(f"{'次数':>4} | {'テーラー係数':>26} | {'glibcの係数':>26} | {'相対差':>10}")
print("-" * 78)
names = [(0, mpf(1)), (1, POLY[2]), (2, POLY[1]), (3, POLY[0])]
for (k, g) in names:
    t = taylor_coeffs[k]
    d = abs(g - t) / t
    print(f"{k:>4} | {mp.nstr(t, 20):>26} | {mp.nstr(g, 20):>26} | {mp.nstr(d, 4):>10}")

print()
print("1次の係数は ln2 に近いが一致しない（第3章で見たとおり）。")
print("次数が上がるほど、ずれが大きくなっている。")

# --------------------------------------------------------------------------
rule("[4] テーラー展開のままだとどれくらい悪いのか")

def taylor_p(t):
    return sum(taylor_coeffs[k] * t**k for k in range(4))

terr, _ = max_rel_err(taylor_p, lambda t: mpf(2) ** t, -HALF, HALF)
print(f"3次テーラー展開の最大相対誤差 : {mp.nstr(terr, 8)}")
print(f"glibcの係数の最大相対誤差     : {mp.nstr(err, 8)}")
print(f"改善率                        : {mp.nstr(terr / err, 6)} 倍")
print()
print(f"テーラーのままだと {mp.nstr(terr / mpf(2)**-34, 4)} × 2^-34 で、")
print(f"目標の 1.69 × 2^-34 に届かない。")
