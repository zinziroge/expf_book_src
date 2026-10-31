/* 第7章: テーブルが 2^(k/N) をどう組み立てているかを確かめる。
 *
 * e_expf.c の該当箇所:
 *     t = T[ki % N];
 *     t += ki << (52 - EXP2F_TABLE_BITS);
 *     s = asdouble (t);
 *
 * テーブルには 2^(i/N) のビット列そのものではなく、そこから (i << 47) を
 * 引いたものが入っている。この引き算がなぜ必要なのかを確かめる。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c sh -c "
 *     gcc -O2 -std=gnu11 -o /tmp/t ch07_minimax/table_trick.c -lm && /tmp/t"
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define N 32
#define SHIFT_BITS (52 - 5)          /* = 47 */

static const double SHIFT = 0x1.8p+52;

/* e_exp2f_data.c の .tab */
static const uint64_t T[N] = {
	0x3ff0000000000000, 0x3fefd9b0d3158574, 0x3fefb5586cf9890f, 0x3fef9301d0125b51,
	0x3fef72b83c7d517b, 0x3fef54873168b9aa, 0x3fef387a6e756238, 0x3fef1e9df51fdee1,
	0x3fef06fe0a31b715, 0x3feef1a7373aa9cb, 0x3feedea64c123422, 0x3feece086061892d,
	0x3feebfdad5362a27, 0x3feeb42b569d4f82, 0x3feeab07dd485429, 0x3feea47eb03a5585,
	0x3feea09e667f3bcd, 0x3fee9f75e8ec5f74, 0x3feea11473eb0187, 0x3feea589994cce13,
	0x3feeace5422aa0db, 0x3feeb737b0cdc5e5, 0x3feec49182a3f090, 0x3feed503b23e255d,
	0x3feee89f995ad3ad, 0x3feeff76f2fb5e47, 0x3fef199bdd85529c, 0x3fef3720dcef9069,
	0x3fef5818dcfba487, 0x3fef7c97337b9b5f, 0x3fefa4afa2a490da, 0x3fefd0765b6e4540,
};

static uint64_t asuint64(double f) { uint64_t u; memcpy(&u, &f, sizeof u); return u; }
static double asdouble(uint64_t i) { double f; memcpy(&f, &i, sizeof f); return f; }

static void rule(const char *s)
{
	printf("\n==========================================================================\n");
	printf("%s\n", s);
	printf("==========================================================================\n");
}

/* glibcと同じ手順で 2^(k/N) を組み立てる */
static double build(int k)
{
	uint64_t ki = asuint64((double)k + SHIFT);
	uint64_t t = T[ki % N];
	t += ki << SHIFT_BITS;
	return asdouble(t);
}

int main(void)
{
	rule("[1] テーブルには 2^(i/N) から (i << 47) を引いた値が入っている");

	printf("%3s | %20s | %20s | %20s\n",
	       "i", "tab[i]", "tab[i] + (i<<47)", "2^(i/32)");
	printf("--------------------------------------------------------------------------\n");
	for (int i = 0; i < N; i += 8) {
		uint64_t restored = T[i] + ((uint64_t)i << SHIFT_BITS);
		printf("%3d | 0x%016llx | %20.17g | %20.17g\n",
		       i, (unsigned long long)T[i],
		       asdouble(restored), exp2((double)i / N));
	}
	printf("\n引き戻すと 2^(i/32) に一致する。\n");

	rule("[2] なぜ引いた形で持つのか");

	printf("k を N で割った商 q と余り m に分ける（k = 32q + m）。\n");
	printf("  k << 47 = (32q + m) << 47 = (q << 52) + (m << 47)\n\n");
	printf("tab[m] = bits(2^(m/32)) - (m << 47) なので、足すと打ち消し合う。\n");
	printf("  tab[m] + (k << 47)\n");
	printf("    = bits(2^(m/32)) - (m<<47) + (q<<52) + (m<<47)\n");
	printf("    = bits(2^(m/32)) + (q<<52)\n\n");
	printf("doubleの指数部はbit52以上にあるので、(q<<52) を足すことは\n");
	printf("指数部に q を足すこと、つまり 2^q 倍することに等しい。\n");
	printf("  -> 2^(m/32) * 2^q = 2^(k/32)\n");
	printf("\nつまり「余りでテーブルを引く」と「商で指数部をずらす」を、\n");
	printf("整数の足し算1回でまとめてやっている。\n");

	rule("[3] 本当に 2^(k/N) になるか（負のkも含めて確認）");

	printf("%8s | %8s | %6s | %24s | %24s | %s\n",
	       "k", "q", "m", "組み立てた値", "exp2(k/32)", "一致");
	printf("--------------------------------------------------------------------------\n");
	{
		const int ks[] = { 0, 1, 16, 31, 32, 33, 64, 100, -1, -32, -33, -100 };
		for (size_t i = 0; i < sizeof ks / sizeof ks[0]; i++) {
			int k = ks[i];
			double got = build(k);
			double want = exp2((double)k / N);
			int q = (int)floor((double)k / N);
			int m = k - q * N;
			printf("%8d | %8d | %6d | %24.17g | %24.17g | %s\n",
			       k, q, m, got, want,
			       asuint64(got) == asuint64(want) ? "OK" : "NG");
		}
	}

	rule("[4] expfで実際に現れる全範囲のkで確認する");

	{
		int ng = 0, total = 0;
		double worst = 0.0;
		int worst_k = 0;
		for (int k = -150 * N; k <= 128 * N; k++) {
			double got = build(k);
			double want = exp2((double)k / N);
			total++;
			if (!isfinite(got) || !isfinite(want))
				continue;
			if (asuint64(got) != asuint64(want)) {
				ng++;
				double rel = fabs((got - want) / want);
				if (rel > worst) { worst = rel; worst_k = k; }
			}
		}
		printf("k の範囲       : %d 〜 %d （第6章で確認した範囲）\n", -150 * N, 128 * N);
		printf("確認した個数   : %d\n", total);
		printf("食い違った個数 : %d\n", ng);
		if (ng) {
			printf("最大相対差     : %.3e (k=%d)\n", worst, worst_k);
			printf("  ※ exp2() 自身の丸め誤差の可能性がある\n");
		} else {
			printf("-> すべて exp2(k/32) とビット単位で一致した。\n");
		}
	}

	rule("[5] テーブルの値そのものの誤差");

	printf("テーブルはdoubleなので、2^(i/32) を丸めた値しか持てない。\n");
	printf("その丸め誤差がどれくらいか見る。\n");
	printf("テーブルの値はすべて 1 以上 2 未満なので、doubleの刻み幅は 2^-52 で一定。\n\n");
	printf("%3s | %24s | %14s\n", "i", "tab[i]を復元した値", "誤差(ULP)");
	printf("--------------------------------------------------------------------------\n");
	{
		/* long double を使って、doubleより高い精度で 2^(i/N) を求めて比べる */
		double worst = 0.0;
		int worst_i = 0, over_half = 0;
		for (int i = 0; i < N; i++) {
			uint64_t restored = T[i] + ((uint64_t)i << SHIFT_BITS);
			double got = asdouble(restored);
			long double want = exp2l((long double)i / N);
			/* テーブルの値は [1,2) にあるので ulp = 2^-52 */
			double ulps = (double)(fabsl((long double)got - want) / 0x1p-52L);
			if (ulps > worst) { worst = ulps; worst_i = i; }
			if (ulps > 0.5) over_half++;
			if (i % 8 == 0)
				printf("%3d | %24.17g | %14.4f\n", i, got, ulps);
		}
		printf("\n最大の誤差   : %.4f ULP (i=%d)\n", worst, worst_i);
		printf("0.5 ULPを超えた項目数: %d\n", over_half);
		if (over_half == 0)
			printf("-> 全32項目が正しく丸められている（correctly rounded）。\n");
	}

	return 0;
}
