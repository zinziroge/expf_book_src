/* 第3章「C言語における数値表記」で使う挙動を実際に確認する。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker build -t expfbook-c docker
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c \
 *       sh -c "gcc -O2 -std=c11 -o /tmp/a ch03_c_numeric/c_numeric.c -lm && /tmp/a"
 *
 * 本文に載せる数値はすべてこのプログラムの出力から取っている。
 */

#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* floatのビットパターンを取り出す。共用体やmemcpyを使うのが安全。 */
static uint32_t bits_f(float x)
{
	uint32_t u;
	memcpy(&u, &x, sizeof u);
	return u;
}

static uint64_t bits_d(double x)
{
	uint64_t u;
	memcpy(&u, &x, sizeof u);
	return u;
}

static void rule(const char *title)
{
	printf("\n==========================================================================\n");
	printf("%s\n", title);
	printf("==========================================================================\n");
}

int main(void)
{
	rule("[1] リテラルに f を付けるかどうかで型が変わる");

	printf("sizeof(0.1)  = %zu  (接尾辞なし -> double)\n", sizeof(0.1));
	printf("sizeof(0.1f) = %zu  (f 付き     -> float)\n", sizeof(0.1f));
	printf("\n");
	printf("0.1  を %%a で表示 : %a\n", 0.1);
	printf("0.1f を %%a で表示 : %a\n", (double)0.1f);
	printf("\n");
	printf("同じ「0.1」でも表している値は違う:\n");
	printf("  (double)0.1  = %.20f\n", 0.1);
	printf("  (double)0.1f = %.20f\n", (double)0.1f);
	printf("  0.1f == 0.1 の判定結果 : %d  (0なら偽)\n", 0.1f == 0.1);
	printf("  ※ 比較の前に 0.1f が double に昇格され、その上で 0.1 と比べられる\n");

	rule("[2] 16進浮動小数点リテラル（glibcのソースで多用される書き方）");

	printf("0x1.8p+52 は 1.5 * 2^52 を意味する:\n");
	printf("  値      = %.1f\n", 0x1.8p+52);
	printf("  16進    = %a\n", 0x1.8p+52);
	printf("  ビット  = 0x%016llx\n", (unsigned long long)bits_d(0x1.8p+52));
	printf("\n");
	printf("glibcのexpfが使う多項式係数（e_exp2f_data.c の .poly）:\n");
	printf("  0x1.c6af84b912394p-5 = %.20e\n", 0x1.c6af84b912394p-5);
	printf("  0x1.ebfce50fac4f3p-3 = %.20e\n", 0x1.ebfce50fac4f3p-3);
	printf("  0x1.62e42ff0c52d6p-1 = %.20e  (これは ln(2) に近い)\n", 0x1.62e42ff0c52d6p-1);
	printf("  参考: ln(2)          = %.20e\n", log(2.0));
	printf("\n");
	printf("expfの引数域の判定に使われる定数（e_expf.c）:\n");
	printf("   0x1.62e42ep6f = %+.7f  (これを超えるとオーバーフロー)\n", (double)0x1.62e42ep6f);
	printf("  -0x1.9fe368p6f = %+.7f  (これを下回るとアンダーフロー)\n", (double)-0x1.9fe368p6f);
	printf("  参考: log(2^128)  = %.7f\n", 128.0 * log(2.0));
	printf("  参考: log(2^-150) = %.7f\n", -150.0 * log(2.0));

	rule("[3] 10進で書くと丸めが1回入る");

	printf("10進リテラルはコンパイル時に最も近いfloatへ丸められる。\n");
	printf("  0.1f のビット : 0x%08x\n", bits_f(0.1f));
	printf("  0.1f の厳密値 : %.24f\n", (double)0.1f);
	printf("16進リテラルなら、書いた値がそのままビットになる（丸めが起きない）。\n");
	printf("  0x1.99999ap-4 のビット : 0x%08x\n", bits_f(0x1.99999ap-4f));
	printf("  一致するか : %d\n", bits_f(0.1f) == bits_f(0x1.99999ap-4f));

	rule("[4] floatで表せない整数");

	float big = 16777217.0f; /* 2^24 + 1 */
	printf("2^24     = %.1f\n", (double)16777216.0f);
	printf("2^24 + 1 = %.1f  <- 表現できずに 2^24 へ丸められる\n", (double)big);
	printf("2^24 + 2 = %.1f  <- これは表現できる\n", (double)16777218.0f);
	printf("（1.0以上2.0未満で間隔が2^-23なので、2^24以上では間隔が2になる）\n");

	rule("[5] 演算がどの精度で行われるか（FLT_EVAL_METHOD）");

	printf("FLT_EVAL_METHOD = %d\n", FLT_EVAL_METHOD);
	printf("  0: floatの演算はfloatのまま行う\n");
	printf("  1: floatの演算をdoubleで行う\n");
	printf("  2: floatの演算をlong doubleで行う\n");
	printf("この値によって、途中結果の精度が変わりうる。\n");

	rule("[6] expf と exp のどちらを呼ぶかで結果が変わりうる");

	printf("float y1 = expf(x);          -> 単精度用の実装\n");
	printf("float y2 = (float)exp(x);    -> 倍精度で計算してからfloatへ丸める\n");
	printf("\n");
	printf("%14s | %12s | %12s | %s\n", "x", "expf(x)", "(float)exp(x)", "同じか");
	printf("--------------------------------------------------------------------------\n");
	{
		const float xs[] = { 1.0f, 10.0f, -5.0f, 0.5f, 87.0f };
		for (size_t i = 0; i < sizeof xs / sizeof xs[0]; i++) {
			float x = xs[i];
			float y1 = expf(x);
			float y2 = (float)exp((double)x);
			printf("%14.6f | %12.6e | %12.6e | %s\n",
			       (double)x, (double)y1, (double)y2,
			       bits_f(y1) == bits_f(y2) ? "yes" : "NO");
		}
	}
	printf("\nここで見た範囲では一致した。食い違う入力があるかどうかは第4章で扱う。\n");

	return 0;
}
