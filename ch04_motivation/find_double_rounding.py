"""第4章: 「doubleで計算してfloatに丸める」と何が起きるかを全数探索で調べる。

調べたいのは次の食い違いである。

    A = (exp(x)を厳密に計算し、直接float32へ正しく丸めた値)
    B = (exp(x)を厳密に計算し、いったんfloat64へ正しく丸め、さらにfloat32へ丸めた値)

AとBが食い違う入力xが実在するなら、それが「二重に丸めたせいで
最終結果がずれる」= double rounding の実例になる。

手順:
  1. numpyでfloat32の入力を全数走査し、float64のexpで概算する。
     結果がfloat32の丸め境界（中点）にきわめて近いものだけを候補として拾う。
  2. 候補だけをmpmathの高精度演算で厳密に判定する。

実行: ../py_tool/.venv/bin/python find_double_rounding.py
"""

import struct
import time

import numpy as np
from mpmath import mp, mpf, exp as mexp

mp.prec = 300      # 2進300bit。判定に必要な分解能(約2^-60)より遥かに高い

# exp(x)が0にもinfにもならない入力域を全部見る。
#   exp(x) >= 2^-150 <=>  x >= -150*ln2 = -103.9721...  (これ未満は0に潰れる)
#   exp(x) <  2^128  <=>  x <   128*ln2 =   88.7228...  (これ以上はinf)
# 非正規化数になる出力（x < -87.3365...）も含めて走査する。
X_LO, X_HI = -103.97208, 88.72283
SUBNORMAL_MIN = 2.0 ** -126     # これ未満の結果はfloat32では非正規化数

# 候補として拾う閾値。float32のulpを1としたときの中点からの距離。
# float64のulpはこの単位で 2^-29 なので、2^-25 は十分に余裕がある。
NEAR = 2.0 ** -25

CHUNK = 1 << 23


def f32_bits(x) -> int:
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def binade(v: mpf) -> int:
    """2^e <= v < 2^(e+1) となるeを返す。"""
    e = int(mp.floor(mp.log(v, 2)))
    while mpf(2) ** e > v:
        e -= 1
    while mpf(2) ** (e + 1) <= v:
        e += 1
    return e


def round_to(v: mpf, prec_bits: int, emin: int):
    """正の高精度値vを、指定精度・最小指数の2進浮動小数点へ最近接偶数丸めする。

    prec_bits: 仮数のbit数（float32なら24、float64なら53）
    emin     : 正規化数の最小指数（float32なら-126、float64なら-1022）
    戻り値: 丸めた結果をmpfで返す（厳密に表現できる値になる）
    """
    e = binade(v)
    # 非正規化数の領域では、刻み幅は 2^(emin - prec_bits + 1) で固定
    shift = max(e - (prec_bits - 1), emin - (prec_bits - 1))
    scaled = v / mpf(2) ** shift
    n = int(mp.floor(scaled))
    frac = scaled - n
    if frac > mpf(1) / 2:
        n += 1
    elif frac == mpf(1) / 2:
        if n % 2 == 1:               # ties to even
            n += 1
    return mpf(n) * mpf(2) ** shift, frac


def scan():
    """float32を全数走査して、丸め境界に極端に近い候補を集める。"""
    lo_bits = f32_bits(X_LO)
    hi_bits = f32_bits(X_HI)

    ranges = [
        # 負側: 符号bitを立てたビットパターン。0x80000000 が -0.0
        ("negative", 0x80000000, 0x80000000 | lo_bits),
        # 正側
        ("positive", 0x00000000, hi_bits),
    ]

    candidates = []
    scanned = 0
    closest = 1.0
    t0 = time.time()
    for name, a, b in ranges:
        for start in range(a, b, CHUNK):
            end = min(start + CHUNK, b)
            u = np.arange(start, end, dtype=np.uint32)
            x32 = u.view(np.float32)
            x64 = x32.astype(np.float64)
            y = np.exp(x64)

            # float32の刻み幅を1とする単位に正規化する。
            # 正規化数の領域では刻み幅が2^(e-24)、非正規化数の領域では2^-149で一定。
            _, e = np.frexp(y)                 # y = m * 2^e, 0.5 <= m < 1
            scaled = np.where(
                y >= SUBNORMAL_MIN,
                np.ldexp(y, 24 - e),           # 正規化数: [2^23, 2^24) に入る
                np.ldexp(y, 149),              # 非正規化数: [1, 2^23) に入る
            )
            frac = scaled - np.floor(scaled)
            d = np.abs(frac - 0.5)             # float32の丸め境界(中点)からの距離

            closest = min(closest, float(d.min()))
            hit = np.nonzero(d < NEAR)[0]
            for i in hit:
                candidates.append(int(u[i]))
            scanned += end - start
        print(f"  {name}: 走査済み {scanned:,} (経過 {time.time() - t0:.1f}s)")

    return candidates, scanned, closest


def verify(bits: int):
    """候補1件を高精度で厳密に判定する。"""
    x = struct.unpack("<f", struct.pack("<I", bits))[0]
    exact = mexp(mpf(x))

    direct, frac32 = round_to(exact, 24, -126)          # 厳密値 -> float32
    via64, _ = round_to(exact, 53, -1022)               # 厳密値 -> float64
    via32, _ = round_to(via64, 24, -126)                # float64 -> float32

    return {
        "bits": bits,
        "x": x,
        "exact": exact,
        "direct": direct,
        "via32": via32,
        "differs": direct != via32,
        "frac32": frac32,       # 中点(0.5)からのずれを見るため
    }


def self_test():
    """検出機構が本当にdouble roundingを見つけられるかを確かめる（陽性対照）。

    1.0 と 1+2^-23 の中点 m=1+2^-24 のわずかに上に値を置く。
      - 厳密値から直接float32へ丸めると 1+2^-23（中点より上だから）
      - いったんfloat64へ丸めるとちょうど m になり、
        そこからfloat32へ丸めると偶数丸めで 1.0 に落ちる
    この食い違いを検出できなければ、探索結果は信用できない。
    """
    m = mpf(1) + mpf(2) ** -24
    z = m + mpf(2) ** -60
    direct, _ = round_to(z, 24, -126)
    via64, _ = round_to(z, 53, -1022)
    via32, _ = round_to(via64, 24, -126)
    assert direct != via32, "陽性対照を検出できていない。判定ロジックが壊れている"
    return float(direct), float(via32)


def main():
    print("=" * 74)
    print("[0] 自己テスト: 人工的なdouble roundingを検出できるか")
    print("=" * 74)
    d, v = self_test()
    print(f"  直接float32へ丸め     : {d!r}")
    print(f"  double経由でfloat32へ : {v!r}")
    print("  -> 食い違いを検出できた。判定ロジックは動作している。")

    print()
    print("=" * 74)
    print("[1] float32の全数走査で、丸め境界に極端に近い入力を集める")
    print("=" * 74)
    print(f"走査範囲: {X_LO} <= x <= {X_HI}")
    print("         （exp(x)が0にもinfにもならない全範囲。非正規化数の結果も含む）")
    print(f"候補の閾値: 丸め境界からの距離 < 2^-25 (float32の刻み幅を1として)")
    print()

    candidates, scanned, closest = scan()
    print()
    print(f"走査した入力の総数     : {scanned:,}")
    print(f"拾った候補の数         : {len(candidates):,}")
    print(f"境界への最接近距離     : {closest:.6e} = 2^{np.log2(closest):.1f}")
    print()

    print("=" * 74)
    print("[2] 候補を高精度演算で厳密に判定する")
    print("=" * 74)

    found = []
    for b in candidates:
        r = verify(b)
        if r["differs"]:
            found.append(r)

    print(f"直接float32へ丸めた結果と、double経由で丸めた結果が食い違った件数: {len(found)}")
    print()

    for r in found:
        x = r["x"]
        print("-" * 74)
        print(f"x           = {x!r}  (0x{r['bits']:08X})")
        print(f"  exp(x)厳密 = {mp.nstr(r['exact'], 25)}")
        print(f"  直接float32へ丸め      : {float(r['direct']):.9e}  (0x{f32_bits(r['direct']):08X})")
        print(f"  double経由でfloat32へ  : {float(r['via32']):.9e}  (0x{f32_bits(r['via32']):08X})")
        diff_ulp = abs(float(r["direct"]) - float(r["via32"]))
        print(f"  差                     : {diff_ulp:.6e}  = 1 ulp")
        print(f"  中点からのずれ          : {mp.nstr(r['frac32'] - mpf(1)/2, 6)} ulp")

    if found:
        print("-" * 74)
        print()
        print("この結果を再現するためのCコード用データ:")
        for r in found:
            print(f"  {{ 0x{r['bits']:08X}u, /* x = {r['x']:.9g} */ }},")


if __name__ == "__main__":
    main()
