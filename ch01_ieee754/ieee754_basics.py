"""第1章「IEEE754の基礎」で使う数値を実際に計算して出力する。

本文に載せる数値はすべてこのスクリプトの出力から取っている。
実行: ../py_tool/.venv/bin/python ieee754_basics.py

注意: 指数eの判定にDecimalのべき乗を使うと、2^-126のように有効桁が
      精度設定を超える場合に丸められて判定を誤る。ここでは必ず
      ビットパターンから厳密に求めている。
"""

import struct
from decimal import Decimal, getcontext
from fractions import Fraction

getcontext().prec = 100

P = 24          # float32の精度（ケチ表現の隠れbitを含めた仮数のbit数）
BIAS = 127
EMIN = -126     # 正規化数の最小指数
SUB_ULP = 2.0 ** (EMIN - (P - 1))   # 非正規化数の間隔 = 2^-149


def f32(x: float) -> float:
    """xを最近接偶数丸めでfloat32に丸め、その値をPythonのfloat(=double)で返す。"""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def bits_of(x: float) -> int:
    """float32としてのビットパターンを32bit整数で返す。"""
    return struct.unpack("<I", struct.pack("<f", x))[0]


def from_bits(b: int) -> float:
    return struct.unpack("<f", struct.pack("<I", b))[0]


def decompose(x: float):
    """float32のビットを 符号 / 指数フィールド / 仮数フィールド に分解する。"""
    b = bits_of(x)
    return b >> 31, (b >> 23) & 0xFF, b & 0x7FFFFF


def binade(x: float) -> int:
    """2^e <= |x| < 2^(e+1) となる整数eを、ビットパターンから厳密に求める。"""
    if x == 0:
        raise ValueError("0には定義しない")
    _, ef, ff = decompose(x)
    if ef != 0:                       # 正規化数
        return ef - BIAS
    # 非正規化数: 仮数の最上位の立っているbitの位置で決まる
    return EMIN - (P - 1) + ff.bit_length() - 1


def ulp(x: float) -> float:
    """本書で採用するulpの定義。

    0でない実数xに対し 2^e <= |x| < 2^(e+1) となるeをとり ulp(x) = 2^(e-23)。
    ただし正規化数の下限を下回る領域では非正規化数の間隔 2^-149 で頭打ちにする。
    """
    if x == 0:
        return SUB_ULP
    return max(2.0 ** (binade(x) - (P - 1)), SUB_ULP)


def rule(title: str):
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


# --------------------------------------------------------------------------
rule("[1] float32のビット分解")

samples = [
    ("1.0", 1.0),
    ("2.0", 2.0),
    ("0.5", 0.5),
    ("-2.0", -2.0),
    ("0.1", f32(0.1)),
    ("3.14", f32(3.14)),
]
print(f"{'value':>7} | {'S':>1} | {'exp field':>9} | {'e':>4} | {'fraction field':>23} | {'hex':>10}")
print("-" * 74)
for name, v in samples:
    s, ef, ff = decompose(v)
    print(f"{name:>7} | {s:>1} | {ef:08b}  | {binade(v):>+4} | {ff:023b} | 0x{bits_of(v):08X}")

# --------------------------------------------------------------------------
rule("[2] float32の代表的な限界値")

FLT_MAX = from_bits(0x7F7FFFFF)
FLT_MIN_NORMAL = from_bits(0x00800000)
FLT_TRUE_MIN = from_bits(0x00000001)
FLT_EPSILON = 2.0 ** -23

for name, v, expr in [
    ("FLT_MAX", FLT_MAX, "(2-2^-23)*2^127"),
    ("FLT_MIN (正規化数の最小)", FLT_MIN_NORMAL, "2^-126"),
    ("非正規化数の最小", FLT_TRUE_MIN, "2^-149"),
    ("FLT_EPSILON", FLT_EPSILON, "2^-23"),
]:
    print(f"{name:<24} = {float(v):.9e}  = {expr:<16} (0x{bits_of(v):08X})")

# --------------------------------------------------------------------------
rule("[3] 0.1はfloat32では正確に表せない")

v = f32(0.1)
print("ソースに書いた 0.1f が実際に表している値（厳密な10進展開）:")
print(f"  {Decimal(v)}")
print(f"  ビットパターン: 0x{bits_of(v):08X}")
diff = Fraction(v) - Fraction(1, 10)
print(f"  10進の0.1との差 : {float(diff):+.6e}")
print(f"  ulp(0.1)        : {ulp(v):.6e}")
print(f"  相対誤差        : {float(abs(diff) / Fraction(1, 10)):.3e}")
print(f"  ulpで測った誤差 : {float(abs(diff) / Fraction(ulp(v))):.4f} ulp")

# --------------------------------------------------------------------------
rule("[4] ulpは値の大きさによって変わる")

print(f"{'x':>14} | {'e':>5} | {'ulp(x)':>15} | {'ulp(x)/x':>12}")
print("-" * 74)
for x in [1.0, 2.0, 0.1, 100.0, 1.0e6, 1.0e30, FLT_MIN_NORMAL, FLT_TRUE_MIN]:
    print(f"{x:>14.6g} | {binade(x):>5} | {ulp(x):>15.6e} | {ulp(x) / x:>12.3e}")

print()
print("正規化数の範囲ではulp(x)/xは 2^-24 〜 2^-23 の間に収まる。")
print(f"  2^-24 = {2.0**-24:.6e} , 2^-23 = {2.0**-23:.6e}")

# --------------------------------------------------------------------------
rule("[5] 1.0以上2.0未満のfloat32は2^23個、間隔は一定")

lo, hi = bits_of(1.0), bits_of(2.0)
print(f"1.0のビット : 0x{lo:08X}")
print(f"2.0のビット : 0x{hi:08X}")
print(f"この区間のfloat32の個数 : {hi - lo} = 2^{(hi - lo).bit_length() - 1}")
print(f"隣り合う値の間隔        : {from_bits(lo + 1) - 1.0:.9e} = 2^-23")
print(f"1.0の次のfloat32        : {Decimal(from_bits(lo + 1))}")

# --------------------------------------------------------------------------
rule("[6] 最近接偶数丸め（round to nearest, ties to even）")

print("ちょうど中間の値をfloat32に丸めるとどちら側に倒れるか。")
for label, val in [
    ("1 + 2^-24", 1.0 + 2.0 ** -24),
    ("(1 + 2^-23) + 2^-24", from_bits(bits_of(1.0) + 1) + 2.0 ** -24),
]:
    r = f32(val)
    print(f"  {label:<20} -> {Decimal(r)}")
    print(f"  {'':<20}    仮数の最下位bit = {bits_of(r) & 1}")
print("どちらも仮数の最下位bitが0になる側へ丸まっている。")

# --------------------------------------------------------------------------
rule("[7] float32の総数と、expfの入力として意味のある範囲")

print(f"float32のビットパターン総数         : 2^32 = {2**32}")
print(f"NaN/Infを除いた有限な値の個数        : {2 * (0xFF * 2**23)} 個")
print("expfは入力が約-87.34を下回ると0に、約88.73を超えるとinfに落ちる。")
print("（この境界値は第9章で実測する）")
