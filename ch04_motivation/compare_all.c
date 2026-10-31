/* 第4章: expf(x) と (float)exp((double)x) が実際に食い違う入力を全数で数える。
 *
 * ここで比べているのは「2つの実装同士」であって、どちらが正しいかではない。
 * 厳密な正解（MPFR）と突き合わせるのは第9章で行う。
 *
 * ビルドと実行（リポジトリルートから）:
 *   docker run --rm -v "$PWD:/work" -w /work expfbook-c \
 *       sh -c "gcc -O2 -std=c11 -o /tmp/c ch04_motivation/compare_all.c -lm && /tmp/c"
 */

#define _POSIX_C_SOURCE 199309L

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static float from_bits(uint32_t u)
{
	float f;
	memcpy(&f, &u, sizeof f);
	return f;
}

static uint32_t to_bits(float f)
{
	uint32_t u;
	memcpy(&u, &f, sizeof u);
	return u;
}

int main(void)
{
	uint64_t total = 0, diff = 0;
	uint32_t first_diff[8];
	int nfirst = 0;
	uint32_t max_gap = 0;

	/* 全ビットパターンを走査する。NaNとInfは除く。 */
	for (uint64_t u = 0; u <= 0xFFFFFFFFull; u++) {
		uint32_t bits = (uint32_t)u;
		float x = from_bits(bits);

		if (isnan(x) || isinf(x))
			continue;

		float y1 = expf(x);
		float y2 = (float)exp((double)x);
		total++;

		if (to_bits(y1) != to_bits(y2)) {
			diff++;
			if (nfirst < 8)
				first_diff[nfirst++] = bits;
			/* 何ULP離れているか（ビットパターンの差で見る） */
			uint32_t b1 = to_bits(y1), b2 = to_bits(y2);
			uint32_t gap = b1 > b2 ? b1 - b2 : b2 - b1;
			if (gap > max_gap)
				max_gap = gap;
		}
	}

	printf("走査した入力（NaN/Infを除く）: %llu\n", (unsigned long long)total);
	printf("expf(x) と (float)exp(x) が食い違った入力: %llu\n",
	       (unsigned long long)diff);
	printf("割合: %.6f %%\n", 100.0 * (double)diff / (double)total);
	printf("食い違ったときの最大の差: %u ULP\n", max_gap);

	if (nfirst > 0) {
		printf("\n最初に見つかった食い違いの例:\n");
		printf("%14s %14s %16s %16s\n", "bits", "x", "expf(x)", "(float)exp(x)");
		for (int i = 0; i < nfirst; i++) {
			float x = from_bits(first_diff[i]);
			printf("0x%08X %14.7g %16.9e %16.9e\n",
			       first_diff[i], (double)x,
			       (double)expf(x), (double)(float)exp((double)x));
		}
	}

	return 0;
}
