#!/bin/sh
# 第1章の導入で使う「floatのバイナリを実際に覗く」実験。
#
# 実行（リポジトリルートから）:
#   docker run --rm -v "$PWD:/work" -w /work expfbook-c \
#       sh ch01_ieee754/run_binary_demo.sh
set -e

cd "$(dirname "$0")"
gcc -O2 -std=c11 -o /tmp/write_float write_float.c
gcc -O2 -std=c11 -o /tmp/read_float  read_float.c

echo "=============================================================="
echo "[A] プログラムが書いたfloatを、バイナリとして覗く"
echo "=============================================================="
for v in 1.0 2.0 0.5 -2.0 1.5; do
	printf '%-6s -> ' "$v"
	/tmp/write_float "$v" | hexdump -v -e '4/1 "%02x " "\n"'
done

echo
echo "=============================================================="
echo "[B] hexdump -C で見た様子（1.0の場合）"
echo "=============================================================="
/tmp/write_float 1.0 > /tmp/one.bin
hexdump -C /tmp/one.bin

echo
echo "=============================================================="
echo "[C] 逆に、手で組み立てたバイトをfloatとして読ませる"
echo "=============================================================="
echo "1.5 を IEEE754 の規則どおりに組み立てると:"
echo "  符号 0 / 指数部 01111111 (=127, つまり2^0) / 仮数部 1000...0"
echo "  -> 0 01111111 10000000000000000000000 = 0x3FC00000"
echo "  -> リトルエンディアンなので、バイト列は 00 00 c0 3f"
echo
printf '書き込むバイト列 : '
printf '\000\000\300\077' | hexdump -v -e '4/1 "%02x " "\n"'
printf 'floatとして読むと: '
printf '\000\000\300\077' | /tmp/read_float

echo
echo "もうひとつ、0xC0000000 (符号1 / 指数部 10000000 / 仮数部 0) を読ませる:"
printf '書き込むバイト列 : '
printf '\000\000\000\300' | hexdump -v -e '4/1 "%02x " "\n"'
printf 'floatとして読むと: '
printf '\000\000\000\300' | /tmp/read_float
