# 1. 提示された16進浮動小数点数の文字列リスト
hex_strings = [
    "0x1.c6af84b912394p-5",
    "0x1.ebfce50fac4f3p-3",
    "0x1.62e42ff0c52d6p-1"
]

print(f"{'Hex Literal':>22} | {'Decimal Value (Standard)':>24} | {'Decimal Value (Full)':>22}")
print("-" * 76)

for h_str in hex_strings:
    # float.fromhex() を使って10進数のfloatに変換
    val = float.fromhex(h_str)
    
    # 普通の表示と、有効数字を多く（20桁）指定した表示
    print(f"{h_str:>22} | {val:<24} | {val:.20f}")