/* 第5章: glibcのexpfを、ソースを読んだ理解にもとづいて自分で書き直したもの。
 *
 * 目的は「読んだつもり」を検証すること。
 * これがglibcのexpfと全float32入力でビット単位一致すれば、
 * 少なくとも処理の流れは正しく追えている、と言える。
 *
 * 元にしたソース:
 *   glibc 2.43 sysdeps/ieee754/flt-32/e_expf.c
 *   glibc 2.43 sysdeps/ieee754/flt-32/e_exp2f_data.c
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c sh -c "
 *     gcc -O2 -std=gnu11 -mfma -mavx2 -o /tmp/m ch05_overview/my_expf.c -lm && /tmp/m"
 *
 * 【重要】コンパイルオプションで結果が変わる。
 *   glibcのx86-64版は e_expf.c を -mfma -mavx2 付きでビルドした __expf_fma を使う
 *   （sysdeps/x86_64/fpu/multiarch/Makefile）。これに合わせないと一致しない。
 *
 *   -std=c11  … 厳密ISOモードでは -ffp-contract=off が既定になり、FMAへの
 *                縮約が起きない。この場合 42.9億通り中2つだけ結果がずれる。
 *   -std=gnu11… 既定が -ffp-contract=fast なので縮約が起き、glibcと完全一致する。
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define N 32                    /* 1 << EXP2F_TABLE_BITS, EXP2F_TABLE_BITS = 5 */

/* e_exp2f_data.c の .tab をそのまま持ってきたもの。
 * tab[i] は 2^(i/N) のビットパターンから (i << (52-5)) を引いた値。 */
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

/* .poly_scaled と .invln2_scaled と .shift */
static const double C[3] = {
	0x1.c6af84b912394p-5 / N / N / N,
	0x1.ebfce50fac4f3p-3 / N / N,
	0x1.62e42ff0c52d6p-1 / N,
};
static const double InvLn2N = 0x1.71547652b82fep+0 * N;
static const double SHIFT   = 0x1.8p+52;

static inline uint32_t asuint(float f)
{
	uint32_t u;
	memcpy(&u, &f, sizeof u);
	return u;
}

static inline uint64_t asuint64(double f)
{
	uint64_t u;
	memcpy(&u, &f, sizeof u);
	return u;
}

static inline double asdouble(uint64_t i)
{
	double f;
	memcpy(&f, &i, sizeof f);
	return f;
}

static inline uint32_t top12(float x)
{
	return asuint(x) >> 20;
}

float my_expf(float x)
{
	uint32_t abstop;
	uint64_t ki, t;
	double kd, xd, z, r, r2, y, s;

	xd = (double)x;
	abstop = top12(x) & 0x7ff;

	/* [手順1] 特殊な入力を入口で弾く */
	if (abstop >= top12(88.0f)) {
		if (asuint(x) == asuint(-INFINITY))
			return 0.0f;
		if (abstop >= top12(INFINITY))
			return x + x;                 /* +inf はそのまま、NaNもNaN */
		if (x > 0x1.62e42ep6f)
			return 0x1p97f * 0x1p97f;     /* オーバーフロー -> +inf */
		if (x < -0x1.9fe368p6f)
			return 0x1p-95f * 0x1p-95f;   /* アンダーフロー -> +0 */
	}

	/* [手順2] x * N/ln2 = k + r の形にする（引数域縮小） */
	z = InvLn2N * xd;

	/* [手順3] z を最も近い整数 k に丸める。
	 * 2^52 の位に足し込むと、仮数の下位が押し出されて整数化される。 */
	kd = (double)(z + SHIFT);
	ki = asuint64(kd);
	kd -= SHIFT;
	r = z - kd;                   /* r は [-1/2, 1/2] に収まる */

	/* [手順4] テーブルから 2^(k/N) を引く。
	 * 下位5bitで表を引き、残りの上位bitは指数部へ直接足し込む。 */
	t = T[ki % N];
	t += ki << (52 - 5);
	s = asdouble(t);

	/* [手順5] 3次多項式で 2^(r/N) を近似する */
	z = C[0] * r + C[1];
	r2 = r * r;
	y = C[2] * r + 1;
	y = z * r2 + y;

	/* [手順6] 掛け合わせて float へ丸める */
	y = y * s;
	return (float)y;
}

/* ---- ここから検証 ---- */

int main(void)
{
	uint64_t total = 0, diff = 0;
	uint32_t examples[5];
	int nex = 0;

	for (uint64_t u = 0; u <= 0xFFFFFFFFull; u++) {
		uint32_t bits = (uint32_t)u;
		float x;
		memcpy(&x, &bits, sizeof x);

		float a = expf(x);
		float b = my_expf(x);
		total++;

		uint32_t ba = asuint(a), bb = asuint(b);
		/* NaN同士はビットが違っても一致とみなす */
		if (isnan(a) && isnan(b))
			continue;
		if (ba != bb) {
			diff++;
			if (nex < 5)
				examples[nex++] = bits;
		}
	}

	printf("走査した入力                    : %llu\n", (unsigned long long)total);
	printf("glibcのexpfと食い違った入力     : %llu\n", (unsigned long long)diff);

	if (diff == 0) {
		printf("-> 全ビットパターンで完全に一致した。\n");
	} else {
		printf("割合: %.6f %%\n", 100.0 * (double)diff / (double)total);
		printf("\n食い違いの例:\n");
		for (int i = 0; i < nex; i++) {
			float x;
			memcpy(&x, &examples[i], sizeof x);
			printf("  x=0x%08X (%.9g): glibc=%.9e mine=%.9e\n",
			       examples[i], (double)x,
			       (double)expf(x), (double)my_expf(x));
		}
	}
	return 0;
}
