/* 引数で受け取った数をfloatとして、そのまま4バイト標準出力へ書き出す。 */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
	if (argc != 2)
		return 1;
	float x = strtof(argv[1], NULL);
	fwrite(&x, sizeof x, 1, stdout);
	return 0;
}
