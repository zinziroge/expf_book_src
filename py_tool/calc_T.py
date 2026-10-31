import struct
from mpmath import mp

# 1. 高精度計算の設定（倍精度より十分に高い精度にする）
mp.prec = 128

# 今回の定数
N = 32
BITS = 5  # 2^5 = 32

def double_to_uint64(val_mp) -> int:
    """mpmathの数値をIEEE 754 倍精度(double)に丸め、64bit整数のビットパターンとして取得"""
    val_float = float(val_mp)
    # '!d' はビッグエンディアンのdouble、'!Q' はunsigned long long (64bit)
    return struct.unpack('!Q', struct.pack('!d', val_float))[0]

print("--- 自作スクリプトによる逆算結果 ---")
generated_table = []

for i in range(N):
    # ① 数学的な 2^(i/N) を高精度で計算
    two_to_the_i_over_n = mp.mpf(2) ** (mp.mpf(i) / mp.mpf(N))
    
    # ② uint(2^(i/N)) : 倍精度浮動小数点数のビットパターン（64bit整数）に変換
    uint_2_i_n = double_to_uint64(two_to_the_i_over_n)
    
    # ③ (i << 52-BITS) : i を指数部の位置に合わせてシフト
    shift_val = i << (52 - BITS)
    
    # ④ tab[i] = uint(2^(i/N)) - (i << 52-BITS) を実行
    # 64bitの範囲に収めるため 0xFFFFFFFFFFFFFFFF でマスク（C言語のオーバーフロー挙動のシミュレート）
    tab_i = (uint_2_i_n - shift_val) & 0xFFFFFFFFFFFFFFFF
    
    generated_table.append(tab_i)
    
    # 8個ごとに改行して16進数で出力
    if i % 4 == 0 and i != 0:
        print()
    print(f"0x{tab_i:016x}, ", end="")

print("\n")

# --- 答え合わせ ---
original_table = [
    0x3ff0000000000000, 0x3fefd9b0d3158574, 0x3fefb5586cf9890f, 0x3fef9301d0125b51,
    0x3fef72b83c7d517b, 0x3fef54873168b9aa, 0x3fef387a6e756238, 0x3fef1e9df51fdee1,
    0x3fef06fe0a31b715, 0x3feef1a7373aa9cb, 0x3feedea64c123422, 0x3feece086061892d,
    0x3feebfdad5362a27, 0x3feeb42b569d4f82, 0x3feeab07dd485429, 0x3feea47eb03a5585,
    0x3feea09e667f3bcd, 0x3fee9f75e8ec5f74, 0x3feea11473eb0187, 0x3feea589994cce13,
    0x3feeace5422aa0db, 0x3feeb737b0cdc5e5, 0x3feec49182a3f090, 0x3feed503b23e255d,
    0x3feee89f995ad3ad, 0x3feeff76f2fb5e47, 0x3fef199bdd85529c, 0x3fef3720dcef9069,
    0x3fef5818dcfba487, 0x3fef7c97337b9b5f, 0x3fefa4afa2a490da, 0x3fefd0765b6e4540,
]

match = (generated_table == original_table)
print(f"オリジナルのテーブルと完全一致したか: {match}")