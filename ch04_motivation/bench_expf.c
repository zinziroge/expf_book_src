/* 第4章: expf(x) と (float)exp((double)x) の速度を実測して比べる。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c \
 *       sh -c "gcc -O2 -std=c11 -o /tmp/b ch04_motivation/bench_expf.c -lm && /tmp/b"
 *
 * 注意:
 *  - 測定値は環境（CPU・glibcのバージョン・仮想化の有無）に強く依存する。
 *    本書では「桁として何倍か」を見る目的でのみ使い、絶対値は参考値として扱う。
 *  - -ffast-math は使わない。使うとコンパイラが (float)exp((double)x) を
 *    expf(x) に置き換えてしまい、比較にならない。
 */

/* clock_gettime を -std=c11（厳密ISO）でも使えるようにする */
#define _POSIX_C_SOURCE 199309L

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N       (1 << 20)   /* 入力の個数 */
#define REPEAT  11          /* 試行回数。中央値ではなく最小値を採る */

static double now_sec(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* 再現性のため、簡単な線形合同法で入力を作る */
static uint32_t rng_state = 12345;
static float next_input(void)
{
	rng_state = rng_state * 1664525u + 1013904223u;
	/* [-80, 80) の範囲に散らす。expfが有限値を返す実用域 */
	return (float)((rng_state >> 8) / 16777216.0 * 160.0 - 80.0);
}

int main(void)
{
	static float xs[N];
	for (int i = 0; i < N; i++)
		xs[i] = next_input();

	double best_expf = 1e30, best_exp = 1e30;
	volatile float sink = 0.0f;

	for (int r = 0; r < REPEAT; r++) {
		/* expf: 単精度用の実装を直接呼ぶ */
		double t0 = now_sec();
		float s1 = 0.0f;
		for (int i = 0; i < N; i++)
			s1 += expf(xs[i]);
		double t1 = now_sec();
		sink = s1;
		if (t1 - t0 < best_expf)
			best_expf = t1 - t0;

		/* (float)exp: 倍精度で計算してからfloatへ丸める */
		t0 = now_sec();
		float s2 = 0.0f;
		for (int i = 0; i < N; i++)
			s2 += (float)exp((double)xs[i]);
		t1 = now_sec();
		sink = s2;
		if (t1 - t0 < best_exp)
			best_exp = t1 - t0;
	}

	(void)sink;

	printf("入力の個数           : %d\n", N);
	printf("試行回数             : %d （最小値を採用）\n", REPEAT);
	printf("\n");
	printf("expf(x)              : %8.2f ns/call\n", best_expf / N * 1e9);
	printf("(float)exp((double)x): %8.2f ns/call\n", best_exp / N * 1e9);
	printf("\n");
	printf("比 ((float)exp / expf) : %.2f 倍\n", best_exp / best_expf);

	return 0;
}
