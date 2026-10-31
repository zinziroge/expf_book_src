/* 標準入力から4バイトずつ読み、floatとして解釈して表示する。 */
#include <stdio.h>

int main(void)
{
	float x;
	while (fread(&x, sizeof x, 1, stdin) == 1)
		printf("%.9g\n", x);
	return 0;
}
