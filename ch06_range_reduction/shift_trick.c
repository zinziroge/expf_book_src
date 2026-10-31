/* 第6章: SHIFT定数(0x1.8p+52)を足すと整数に丸まる仕掛けを確かめる。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c sh -c "
 *     gcc -O2 -std=gnu11 -o /tmp/s ch06_range_reduction/shift_trick.c -lm && /tmp/s"
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define N 32
static const double SHIFT = 0x1.8p+52;          /* 1.5 * 2^52 */
static const double InvLn2N = 0x1.71547652b82fep+0 * N;

static uint64_t asuint64(double f)
{
	uint64_t u;
	memcpy(&u, &f, sizeof u);
	return u;
}

static double asdouble(uint64_t i)
{
	double f;
	memcpy(&f, &i, sizeof f);
	return f;
}

static void rule(const char *s)
{
	printf("\n==========================================================================\n");
	printf("%s\n", s);
	printf("==========================================================================\n");
}

int main(void)
{
	rule("[1] SHIFTの正体と、その近辺での刻み幅");

	printf("SHIFT = 0x1.8p+52 = %.1f\n", SHIFT);
	printf("      = 1.5 * 2^52 = %.1f\n", 1.5 * 4503599627370496.0);
	printf("  ビット: 0x%016llx\n", (unsigned long long)asuint64(SHIFT));
	printf("\n");
	printf("この値は 2^52 以上 2^53 未満にある。\n");
	printf("  2^52 = %.1f\n", 4503599627370496.0);
	printf("  2^53 = %.1f\n", 9007199254740992.0);
	printf("doubleの仮数は52bitなので、この範囲では刻み幅がちょうど1になる。\n");
	printf("  SHIFTの次のdouble - SHIFT = %.1f\n",
	       asdouble(asuint64(SHIFT) + 1) - SHIFT);
	printf("-> つまり、この付近では小数を表現できない。足すと必ず整数へ丸まる。\n");

	rule("[2] z + SHIFT で本当に整数へ丸まるか");

	printf("%12s | %20s | %8s | %10s\n", "z", "z + SHIFT", "kd", "r = z - kd");
	printf("--------------------------------------------------------------------------\n");
	{
		const double zs[] = { 3.2, 3.7, -3.2, -3.7, 0.5, 1.5, 2.5, -0.5 };
		for (size_t i = 0; i < sizeof zs / sizeof zs[0]; i++) {
			double z = zs[i];
			double kd = z + SHIFT;
			double k = kd - SHIFT;
			printf("%12.1f | %20.1f | %8.0f | %10.1f\n", z, kd, k, z - k);
		}
	}
	printf("\n0.5 は 0 へ、1.5 は 2 へ、2.5 は 2 へ丸まっている。\n");
	printf("ちょうど中間の値が偶数側に倒れる = 最近接偶数丸め（第1章）。\n");
	printf("この丸め方のおかげで |r| <= 1/2 が保証される。\n");

	rule("[3] ビット列の下位に k がそのまま入っている");

	printf("kd = SHIFT + k のビット列は 0x4338000000000000 + k になるはず。\n\n");
	printf("%8s | %20s | %18s | %10s\n", "k", "kd", "asuint64(kd)", "下位5bit");
	printf("--------------------------------------------------------------------------\n");
	{
		const int ks[] = { 0, 1, 2, 31, 32, 33, -1, -2, -32, -33 };
		for (size_t i = 0; i < sizeof ks / sizeof ks[0]; i++) {
			int k = ks[i];
			double kd = (double)k + SHIFT;
			uint64_t ki = asuint64(kd);
			uint64_t base = 0x4338000000000000ull;
			printf("%8d | %20.1f | 0x%016llx | %10llu%s\n",
			       k, kd, (unsigned long long)ki,
			       (unsigned long long)(ki % N),
			       (ki == base + (uint64_t)(int64_t)k) ? "" : "  <- 想定外");
		}
	}
	printf("\n負のkでも、符号なし整数として下位bitを見れば k mod 32 が得られている。\n");
	printf("  例: k=-1 のとき下位5bit = 31 = (-1) mod 32\n");

	rule("[4] この技法が使える z の範囲");

	printf("z + SHIFT が 2^52 以上 2^53 未満に留まる限り、刻み幅は1のまま。\n");
	printf("  下限を割る z = %.1f\n", 4503599627370496.0 - 0x1.8p+52);
	printf("  上限を超える z = %.1f\n", 9007199254740992.0 - 0x1.8p+52);
	printf("つまり |z| が約 2^51 までなら安全。\n\n");

	printf("expfで実際に現れる z の範囲を確かめる。\n");
	printf("  z = x * InvLn2N,  InvLn2N = %.6f\n", InvLn2N);
	{
		double xlo = -103.97208, xhi = 88.72283;
		printf("  x = %.5f のとき z = %.2f  ( = -150*N = %d )\n",
		       xlo, xlo * InvLn2N, -150 * N);
		printf("  x = %.5f のとき z = %.2f  ( =  128*N = %d )\n",
		       xhi, xhi * InvLn2N, 128 * N);
	}
	printf("十分に余裕がある。\n");
	printf("ソースのコメントにある \"the result is in [-150*N, 128*N]\" と一致した。\n");

	rule("[5] なぜ 1.0*2^52 ではなく 1.5*2^52 なのか");

	printf("仮に SHIFT = 2^52 とすると、z が負のとき和が 2^52 を下回る。\n");
	printf("そこは1つ下のbinadeで、刻み幅が 0.5 になってしまう。\n\n");
	{
		double bad = 4503599627370496.0;     /* 2^52 */
		printf("  SHIFT=2^52, z=-3.7 のとき: %.1f + (-3.7) = %.4f\n",
		       bad, bad + (-3.7));
		printf("    -> kd - SHIFT = %.4f （整数になっていない）\n",
		       (bad + (-3.7)) - bad);
		printf("  SHIFT=1.5*2^52, z=-3.7 のとき: kd - SHIFT = %.4f\n",
		       ((-3.7) + SHIFT) - SHIFT);
	}
	printf("\n1.5倍しておくことで、下側にも 2^51 ぶんの余裕ができる。\n");

	return 0;
}
