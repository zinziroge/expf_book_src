/* 第7章: 多項式の係数を sollya で求めたものに差し替えると、
 * expf の結果が何個変わるのかを全数で数える。
 *
 * glibcの係数と、sollyaのfpminimaxが出した係数は上位10桁ほどまで一致するが
 * ビットは違う。その差が最終結果に効くのかを見る。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c sh -c "
 *     gcc -O2 -std=gnu11 -mfma -mavx2 -o /tmp/w ch07_minimax/swap_coeffs.c -lm && /tmp/w"
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define N 32

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

/* glibc の係数（e_exp2f_data.c の .poly） */
static const double G3 = 0x1.c6af84b912394p-5;
static const double G2 = 0x1.ebfce50fac4f3p-3;
static const double G1 = 0x1.62e42ff0c52d6p-1;

/* sollya の fpminimax が出した係数
 * fpminimax(2^x, [|1,2,3|], [|D,D,D|], [-1/64;1/64], relative, 1) */
static const double S3 = 0x1.c6af84c6bb6bdp-5;
static const double S2 = 0x1.ebfce50fafedap-3;
static const double S1 = 0x1.62e42ff0c51fcp-1;

static const double InvLn2N = 0x1.71547652b82fep+0 * N;
static const double SHIFT = 0x1.8p+52;

static uint32_t asuint(float f) { uint32_t u; memcpy(&u, &f, sizeof u); return u; }
static uint64_t asuint64(double f) { uint64_t u; memcpy(&u, &f, sizeof u); return u; }
static double asdouble(uint64_t i) { double f; memcpy(&f, &i, sizeof f); return f; }
static uint32_t top12(float x) { return asuint(x) >> 20; }

/* c3,c2,c1 を差し替えられるようにした expf */
static float expf_with(float x, double c3, double c2, double c1)
{
	uint32_t abstop;
	uint64_t ki, t;
	double kd, xd, z, r, r2, y, s;

	xd = (double)x;
	abstop = top12(x) & 0x7ff;
	if (abstop >= top12(88.0f)) {
		if (asuint(x) == asuint(-INFINITY)) return 0.0f;
		if (abstop >= top12(INFINITY)) return x + x;
		if (x > 0x1.62e42ep6f) return 0x1p97f * 0x1p97f;
		if (x < -0x1.9fe368p6f) return 0x1p-95f * 0x1p-95f;
	}

	z = InvLn2N * xd;
	kd = (double)(z + SHIFT);
	ki = asuint64(kd);
	kd -= SHIFT;
	r = z - kd;

	t = T[ki % N];
	t += ki << (52 - 5);
	s = asdouble(t);

	/* poly_scaled 相当のスケーリングをその場で行う */
	z = (c3 / N / N / N) * r + (c2 / N / N);
	r2 = r * r;
	y = (c1 / N) * r + 1;
	y = z * r2 + y;
	y = y * s;
	return (float)y;
}

int main(void)
{
	uint64_t total = 0, diff_glibc = 0, diff_between = 0;
	uint32_t ex[5];
	int nex = 0;

	for (uint64_t u = 0; u <= 0xFFFFFFFFull; u++) {
		uint32_t bits = (uint32_t)u;
		float x;
		memcpy(&x, &bits, sizeof x);
		if (isnan(x) || isinf(x)) continue;

		float ref = expf(x);
		float a = expf_with(x, G3, G2, G1);   /* glibcの係数 */
		float b = expf_with(x, S3, S2, S1);   /* sollyaの係数 */
		total++;

		if (asuint(a) != asuint(ref)) diff_glibc++;
		if (asuint(a) != asuint(b)) {
			diff_between++;
			if (nex < 5) ex[nex++] = bits;
		}
	}

	printf("走査した入力                              : %llu\n",
	       (unsigned long long)total);
	printf("自前実装(glibc係数) と glibcのexpf の相違 : %llu\n",
	       (unsigned long long)diff_glibc);
	printf("glibc係数 と sollya係数 の結果の相違      : %llu\n",
	       (unsigned long long)diff_between);
	printf("  割合: %.6f %%\n", 100.0 * (double)diff_between / (double)total);

	if (nex > 0) {
		printf("\n係数の違いで結果が変わった入力の例:\n");
		for (int i = 0; i < nex; i++) {
			float x;
			memcpy(&x, &ex[i], sizeof x);
			printf("  x=0x%08X (%14.7g): glibc係数=%.9e sollya係数=%.9e\n",
			       ex[i], (double)x,
			       (double)expf_with(x, G3, G2, G1),
			       (double)expf_with(x, S3, S2, S1));
		}
	}
	return 0;
}
