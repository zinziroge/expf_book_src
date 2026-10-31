import struct
import matplotlib.pyplot as plt

# 1. 提示された64bit浮動小数点数（倍精度）のビットパターン
hex_data = [
    0x3ff0000000000000, 0x3fefd9b0d3158574, 0x3fefb5586cf9890f, 0x3fef9301d0125b51,
    0x3fef72b83c7d517b, 0x3fef54873168b9aa, 0x3fef387a6e756238, 0x3fef1e9df51fdee1,
    0x3fef06fe0a31b715, 0x3feef1a7373aa9cb, 0x3feedea64c123422, 0x3feece086061892d,
    0x3feebfdad5362a27, 0x3feeb42b569d4f82, 0x3feeab07dd485429, 0x3feea47eb03a5585,
    0x3feea09e667f3bcd, 0x3fee9f75e8ec5f74, 0x3feea11473eb0187, 0x3feea589994cce13,
    0x3feeace5422aa0db, 0x3feeb737b0cdc5e5, 0x3feec49182a3f090, 0x3feed503b23e255d,
    0x3feee89f995ad3ad, 0x3feeff76f2fb5e47, 0x3fef199bdd85529c, 0x3fef3720dcef9069,
    0x3fef5818dcfba487, 0x3fef7c97337b9b5f, 0x3fefa4afa2a490da, 0x3fefd0765b6e4540,
]

def bits_to_double(b: int) -> float:
    """64bitの整数ビットパターンをPythonのfloat(Cのdouble相当)に変換"""
    # '!Q' はビッグエンディアンのunsigned long long (8バイト)
    # '!d' はビッグエンディアンのdouble (8バイト)
    return struct.unpack('!d', struct.pack('!Q', b))[0]

# 2. 10進数の小数に変換
float_values = [bits_to_double(b) for b in hex_data]

# 3. ターミナルへの出力（インデックス、16進表現、10進数表現）
print(f"{'Index':>5} | {'Hex Pattern':>18} | {'Decimal Value':>22}")
print("-" * 53)
for idx, (b, f) in enumerate(zip(hex_data, float_values)):
    print(f"{idx:5d} | 0x{b:016x} | {f:.18f}")

# 4. matplotlibを使用したグラフ化
plt.figure(figsize=(10, 6))
plt.plot(float_values, marker='o', linestyle='-', color='b', label='Table Value')

# グラフの装飾
plt.title("Visualization of Constant Table Values (64bit float)", fontsize=14)
plt.xlabel("Table Index", fontsize=12)
plt.ylabel("Value (Decimal)", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# グラフを表示
plt.show()