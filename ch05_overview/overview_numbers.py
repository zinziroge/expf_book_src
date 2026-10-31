"""第5章の説明で使う数値を実際に計算して出力する。

実行: ../py_tool/.venv/bin/python overview_numbers.py
"""

import struct

from mpmath import mp, mpf, log as mlog, exp as mexp

mp.dps = 50

N = 32


def f32_bits(x) -> int:
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def top12(x) -> int:
    return f32_bits(x) >> 20


def rule(title):
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


# --------------------------------------------------------------------------
rule("[1] 手順1: top12 による大きさの判定")

print(f"{'値':>12} | {'32bit':>10} | {'top12':>6} | {'& 0x7ff':>8}")
print("-" * 74)
for name, v in [("88.0f", 88.0), ("-88.0f", -88.0), ("1.0f", 1.0),
                ("-1.0f", -1.0), ("100.0f", 100.0), ("inf", float("inf"))]:
    t = top12(v)
    print(f"{name:>12} | 0x{f32_bits(v):08X} | 0x{t:04X} | 0x{t & 0x7FF:04X}")

print()
print("符号bitはtop12の最上位に来るので、& 0x7ff で落とすと")
print("絶対値の大きさだけを1つの整数で比較できる。")
print(f"  top12(88.0f) & 0x7ff = 0x{top12(88.0) & 0x7FF:X} = {top12(88.0) & 0x7FF}")

# --------------------------------------------------------------------------
rule("[2] 手順2: 引数域縮小で使う定数")

ln2 = mlog(2)
invln2n = N / ln2
print(f"ln(2)        = {mp.nstr(ln2, 20)}")
print(f"N / ln(2)    = {mp.nstr(invln2n, 20)}   (N = {N})")
print(f"ソース上の値 InvLn2N = 0x1.71547652b82fep+0 * N")
print(f"             = {float.fromhex('0x1.71547652b82fep+0') * N!r}")
print(f"  1/ln(2)    = {mp.nstr(1 / ln2, 20)}")

# --------------------------------------------------------------------------
rule("[3] 手順2: rはどれくらい狭い範囲に収まるか")

print("z = x * N/ln2 を整数kと端数rに分ける。丸めが最近接なので |r| <= 1/2。")
print()
print(f"  |r|     <= 1/2  = {0.5}")
print(f"  |r/N|   <= 1/(2N) = 1/{2*N} = {mp.nstr(mpf(1)/(2*N), 10)}")
print()
print("この r/N が 2^(r/N) の指数になる。振れ幅は次のとおり。")
lo = mpf(2) ** (mpf(-1) / (2 * N))
hi = mpf(2) ** (mpf(1) / (2 * N))
print(f"  2^(-1/{2*N}) = {mp.nstr(lo, 12)}")
print(f"  2^(+1/{2*N}) = {mp.nstr(hi, 12)}")
print(f"  -> 2^(r/N) は {mp.nstr(lo, 8)} 〜 {mp.nstr(hi, 8)} の範囲、つまり1のごく近く")

print()
print("N倍しなかった場合（z = x/ln2 をそのまま整数と端数に分ける）と比べる。")
lo0 = mpf(2) ** mpf("-0.5")
hi0 = mpf(2) ** mpf("0.5")
print(f"  N無し: |r| <= 1/2   なので 2^r は {mp.nstr(lo0, 10)} 〜 {mp.nstr(hi0, 10)}")
print(f"  N=32 : |r/N| <= 1/64 なので 2^(r/N) は {mp.nstr(lo, 10)} 〜 {mp.nstr(hi, 10)}")
print(f"  幅の比: {mp.nstr((hi0 - lo0) / (hi - lo), 6)} 倍せまくなっている")

print()
print("参考: 1/ln2 乗すると本当に e になるか")
print(f"  1/ln2     = {mp.nstr(1 / ln2, 20)}")
print(f"  2^(1/ln2) = {mp.nstr(mpf(2) ** (1 / ln2), 20)}")
print(f"  e         = {mp.nstr(mexp(1), 20)}")

print()
print("参考: 区間縮小をしない場合、xの範囲は約 -103.97 〜 88.72 だった（第3章）。")
print(f"      縮小後の指数の幅は ±1/{2*N} なので、")
print(f"      約 {float(88.72 + 103.97):.1f} の幅が {float(mpf(1)/N):.5f} の幅に縮んでいる。")

# --------------------------------------------------------------------------
rule("[4] 手順4: テーブルの中身は本当に 2^(i/N) か")

TAB = [
    0x3FF0000000000000, 0x3FEFD9B0D3158574, 0x3FEFB5586CF9890F, 0x3FEF9301D0125B51,
    0x3FEF72B83C7D517B, 0x3FEF54873168B9AA, 0x3FEF387A6E756238, 0x3FEF1E9DF51FDEE1,
    0x3FEF06FE0A31B715, 0x3FEEF1A7373AA9CB, 0x3FEEDEA64C123422, 0x3FEECE086061892D,
    0x3FEEBFDAD5362A27, 0x3FEEB42B569D4F82, 0x3FEEAB07DD485429, 0x3FEEA47EB03A5585,
    0x3FEEA09E667F3BCD, 0x3FEE9F75E8EC5F74, 0x3FEEA11473EB0187, 0x3FEEA589994CCE13,
    0x3FEEACE5422AA0DB, 0x3FEEB737B0CDC5E5, 0x3FEEC49182A3F090, 0x3FEED503B23E255D,
    0x3FEEE89F995AD3AD, 0x3FEEFF76F2FB5E47, 0x3FEF199BDD85529C, 0x3FEF3720DCEF9069,
    0x3FEF5818DCFBA487, 0x3FEF7C97337B9B5F, 0x3FEFA4AFA2A490DA, 0x3FEFD0765B6E4540,
]

print("tab[i] は 2^(i/N) のビットから (i << 47) を引いた値、とコメントにある。")
print("足し戻して確かめる。")
print()
print(f"{'i':>3} | {'tab[i]+(i<<47) を doubleで読む':>30} | {'2^(i/32)':>22} | 一致")
print("-" * 74)
worst = 0.0
for i in [0, 1, 8, 16, 31]:
    v = struct.unpack("<d", struct.pack("<Q", (TAB[i] + (i << 47)) & 0xFFFFFFFFFFFFFFFF))[0]
    want = mpf(2) ** (mpf(i) / N)
    rel = abs((mpf(v) - want) / want)
    worst = max(worst, float(rel))
    print(f"{i:>3} | {v!r:>30} | {mp.nstr(want, 16):>22} | {'OK' if rel < mpf(10)**-15 else 'NG'}")

print()
print(f"全32エントリでの最大相対差: ", end="")
worst_all = 0.0
for i in range(N):
    v = struct.unpack("<d", struct.pack("<Q", (TAB[i] + (i << 47)) & 0xFFFFFFFFFFFFFFFF))[0]
    want = mpf(2) ** (mpf(i) / N)
    worst_all = max(worst_all, float(abs((mpf(v) - want) / want)))
print(f"{worst_all:.3e}")
print("doubleの丸め誤差の範囲で一致している。テーブルの読み方は合っていた。")
