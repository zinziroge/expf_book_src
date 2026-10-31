/* 第8章: expf の誤差を、MPFRの高精度計算を「正解」として全数で測る。
 *
 * 測るもの:
 *   - expf(x)              … glibcの単精度実装
 *   - (float)exp((double)x) … 倍精度で計算してfloatへ丸めたもの
 * を、厳密な e^x を float32 へ正しく丸めた値と突き合わせる。
 *
 * 走査範囲は結果が正規化数になる入力に限る（本書は非正規化数を扱わない）。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c sh -c "
 *     gcc -O2 -std=gnu11 -fopenmp -o /tmp/u ch08_ulp/ulp_scan.c -lmpfr -lgmp -lm
 *     && /tmp/u"
 *
 * 引数に数値を渡すと、その個数だけ間引いて走査する（動作確認用）。
 *   /tmp/u 1000    -> 1000個に1個だけ調べる
 */

#include <math.h>
#include <mpfr.h>
#include <omp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PREC 64           /* MPFRの精度。float32の24bitに対し十分な余裕 */
#define NBINS 512         /* 図を描くためにx軸を分ける数 */

/* 結果が正規化数になる入力の範囲（第3章・第6章で確認した値） */
#define X_LO (-87.33654f)
#define X_HI (88.72283f)

static uint32_t asuint(float f) { uint32_t u; memcpy(&u, &f, sizeof u); return u; }
static float asfloat(uint32_t u) { float f; memcpy(&f, &u, sizeof f); return f; }

struct acc {
	double max_expf, max_exp;      /* 最大ULP誤差 */
	uint32_t arg_expf, arg_exp;    /* そのときの入力 */
	uint64_t wrong_expf, wrong_exp;/* 正しく丸めた値と違った個数 */
	uint64_t total;
	double *bin_expf, *bin_exp;    /* 区間ごとの最大ULP誤差 */
};

int main(int argc, char **argv)
{
	long stride = 1;
	if (argc > 1)
		stride = atol(argv[1]);
	if (stride < 1)
		stride = 1;

	const uint32_t lo_pos = 0;                    /* +0.0 */
	const uint32_t hi_pos = asuint(X_HI);
	const uint32_t lo_neg = 0x80000000u;          /* -0.0 */
	const uint32_t hi_neg = asuint(X_LO);

	int nthreads = omp_get_max_threads();
	struct acc *accs = calloc(nthreads, sizeof *accs);
	for (int i = 0; i < nthreads; i++) {
		accs[i].bin_expf = calloc(NBINS, sizeof(double));
		accs[i].bin_exp = calloc(NBINS, sizeof(double));
	}

	double t0 = omp_get_wtime();

	/* 正の側と負の側を続けて走査する */
	for (int side = 0; side < 2; side++) {
		uint32_t lo = side ? lo_neg : lo_pos;
		uint32_t hi = side ? hi_neg : hi_pos;

#pragma omp parallel
		{
			int tid = omp_get_thread_num();
			struct acc *a = &accs[tid];
			mpfr_t y, diff;
			mpfr_inits2(PREC, y, diff, (mpfr_ptr)0);

#pragma omp for schedule(static)
			for (int64_t u = lo; u <= (int64_t)hi; u += stride) {
				float x = asfloat((uint32_t)u);

				/* 厳密な e^x を高精度で求める */
				mpfr_set_flt(y, x, MPFR_RNDN);
				mpfr_exp(y, y, MPFR_RNDN);

				/* 正しく丸めたfloat32 */
				float correct = mpfr_get_flt(y, MPFR_RNDN);

				/* ulp(正解) を求める。
				 * mpfr_get_exp は y = m * 2^e (0.5<=m<1) の e を返すので、
				 * 2^(E) <= y < 2^(E+1) となる E は e-1 になる。 */
				mpfr_exp_t E = mpfr_get_exp(y) - 1;

				float v1 = expf(x);
				float v2 = (float)exp((double)x);

				/* |v - exact| / ulp を求める */
				mpfr_set_flt(diff, v1, MPFR_RNDN);
				mpfr_sub(diff, diff, y, MPFR_RNDN);
				mpfr_abs(diff, diff, MPFR_RNDN);
				mpfr_mul_2si(diff, diff, -(long)(E - 23), MPFR_RNDN);
				double e1 = mpfr_get_d(diff, MPFR_RNDN);

				mpfr_set_flt(diff, v2, MPFR_RNDN);
				mpfr_sub(diff, diff, y, MPFR_RNDN);
				mpfr_abs(diff, diff, MPFR_RNDN);
				mpfr_mul_2si(diff, diff, -(long)(E - 23), MPFR_RNDN);
				double e2 = mpfr_get_d(diff, MPFR_RNDN);

				a->total++;
				if (asuint(v1) != asuint(correct)) a->wrong_expf++;
				if (asuint(v2) != asuint(correct)) a->wrong_exp++;
				if (e1 > a->max_expf) { a->max_expf = e1; a->arg_expf = (uint32_t)u; }
				if (e2 > a->max_exp) { a->max_exp = e2; a->arg_exp = (uint32_t)u; }

				int b = (int)((x - X_LO) / (X_HI - X_LO) * NBINS);
				if (b < 0) b = 0;
				if (b >= NBINS) b = NBINS - 1;
				if (e1 > a->bin_expf[b]) a->bin_expf[b] = e1;
				if (e2 > a->bin_exp[b]) a->bin_exp[b] = e2;
			}
			mpfr_clears(y, diff, (mpfr_ptr)0);
		}
	}

	double elapsed = omp_get_wtime() - t0;

	/* スレッドごとの結果をまとめる */
	struct acc r = {0};
	r.bin_expf = calloc(NBINS, sizeof(double));
	r.bin_exp = calloc(NBINS, sizeof(double));
	for (int i = 0; i < nthreads; i++) {
		r.total += accs[i].total;
		r.wrong_expf += accs[i].wrong_expf;
		r.wrong_exp += accs[i].wrong_exp;
		if (accs[i].max_expf > r.max_expf) {
			r.max_expf = accs[i].max_expf; r.arg_expf = accs[i].arg_expf;
		}
		if (accs[i].max_exp > r.max_exp) {
			r.max_exp = accs[i].max_exp; r.arg_exp = accs[i].arg_exp;
		}
		for (int b = 0; b < NBINS; b++) {
			if (accs[i].bin_expf[b] > r.bin_expf[b]) r.bin_expf[b] = accs[i].bin_expf[b];
			if (accs[i].bin_exp[b] > r.bin_exp[b]) r.bin_exp[b] = accs[i].bin_exp[b];
		}
	}

	printf("==========================================================================\n");
	printf("MPFR(%dbit)を正解として、全float32入力でULP誤差を測る\n", PREC);
	printf("==========================================================================\n");
	printf("走査範囲   : %.5f <= x <= %.5f （結果が正規化数になる範囲）\n",
	       (double)X_LO, (double)X_HI);
	printf("間引き     : %ld （1なら全数）\n", stride);
	printf("走査した数 : %llu\n", (unsigned long long)r.total);
	printf("スレッド数 : %d\n", nthreads);
	printf("所要時間   : %.1f 秒\n", elapsed);
	printf("\n");
	printf("%-24s | %12s | %14s | %s\n",
	       "実装", "最大ULP誤差", "正しく丸めた", "その割合");
	printf("%-24s | %12s | %14s | %s\n", "", "", "値と違った数", "");
	printf("--------------------------------------------------------------------------\n");
	printf("%-24s | %12.4f | %14llu | %.6f %%\n", "expf(x)",
	       r.max_expf, (unsigned long long)r.wrong_expf,
	       100.0 * (double)r.wrong_expf / (double)r.total);
	printf("%-24s | %12.4f | %14llu | %.6f %%\n", "(float)exp((double)x)",
	       r.max_exp, (unsigned long long)r.wrong_exp,
	       100.0 * (double)r.wrong_exp / (double)r.total);

	printf("\n最大誤差を出した入力:\n");
	{
		float x1 = asfloat(r.arg_expf), x2 = asfloat(r.arg_exp);
		printf("  expf         : x = %.9g (0x%08X)  expf(x) = %.9e\n",
		       (double)x1, r.arg_expf, (double)expf(x1));
		printf("  (float)exp   : x = %.9g (0x%08X)  (float)exp(x) = %.9e\n",
		       (double)x2, r.arg_exp, (double)(float)exp((double)x2));
	}

	/* glibcのコメントにある Wrong count: 170635 と突き合わせるため、
	 * 結果が非正規化数になる領域（x < -87.3365）も数えてみる。
	 * ここではULP誤差は測らず、正しく丸めた値と一致するかだけを見る。
	 * （本書は非正規化数を扱わないが、個数の食い違いの原因を確かめるため） */
	if (stride == 1) {
		uint64_t sub_wrong_expf = 0, sub_wrong_exp = 0, sub_total = 0;
		uint32_t sub_lo = asuint(X_LO);           /* -87.33654 */
		uint32_t sub_hi = asuint(-103.97208f);    /* これ未満は0に潰れる */

#pragma omp parallel
		{
			mpfr_t y;
			mpfr_init2(y, PREC);
			uint64_t w1 = 0, w2 = 0, n = 0;
#pragma omp for schedule(static) nowait
			for (int64_t u = sub_lo; u <= (int64_t)sub_hi; u++) {
				float x = asfloat((uint32_t)u);
				mpfr_set_flt(y, x, MPFR_RNDN);
				mpfr_exp(y, y, MPFR_RNDN);
				float correct = mpfr_get_flt(y, MPFR_RNDN);
				n++;
				if (asuint(expf(x)) != asuint(correct)) w1++;
				if (asuint((float)exp((double)x)) != asuint(correct)) w2++;
			}
#pragma omp critical
			{
				sub_wrong_expf += w1; sub_wrong_exp += w2; sub_total += n;
			}
			mpfr_clear(y);
		}

		printf("\n--------------------------------------------------------------------------\n");
		printf("参考: 結果が非正規化数になる領域（本書の対象外）も数えた場合\n");
		printf("--------------------------------------------------------------------------\n");
		printf("追加で走査した数            : %llu\n", (unsigned long long)sub_total);
		printf("expf が外した数（この領域）  : %llu\n", (unsigned long long)sub_wrong_expf);
		printf("(float)exp が外した数        : %llu\n", (unsigned long long)sub_wrong_exp);
		printf("expf の合計                  : %llu\n",
		       (unsigned long long)(r.wrong_expf + sub_wrong_expf));
		printf("  （glibcのコメントの値       : 170635）\n");
	}

	/* 図を描くためのデータを書き出す */
	{
		FILE *fp = fopen("ch08_ulp/ulp_bins.csv", "w");
		if (fp) {
			fprintf(fp, "x,expf_max_ulp,exp_max_ulp\n");
			for (int b = 0; b < NBINS; b++) {
				double x = X_LO + (X_HI - X_LO) * (b + 0.5) / NBINS;
				fprintf(fp, "%.6f,%.6f,%.6f\n", x, r.bin_expf[b], r.bin_exp[b]);
			}
			fclose(fp);
			printf("\n区間ごとの最大ULP誤差を ch08_ulp/ulp_bins.csv に書き出した。\n");
		}
	}

	return 0;
}
