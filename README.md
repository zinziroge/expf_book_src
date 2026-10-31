# expf_book_src — 『glibc expf を読む』検証コード

本文に出てくる数値・図は、すべてここにあるコードを実際に実行して得たものです。
机上の理論値や記憶による数値は本文に書かない、という方針で運用しています。

## 実行環境

| 用途 | 使うもの | 備考 |
|---|---|---|
| 高精度演算（正解値） | Python + mpmath | `py_tool/.venv` にインストール済み |
| 全数探索の高速化 | numpy | 同上 |
| ミニマックス近似 | sollya | `apt-get install sollya`（v8.0で確認） |
| C言語の挙動確認 | gcc + glibc | Docker（`docker/Dockerfile`） |
| 作図 | matplotlib | 日本語フォントが無い環境のため図中は英語表記 |

Python環境は次で実行します（uvで作られた venv をそのまま使用）。

```bash
py_tool/.venv/bin/python <script>
```

C環境は最初に一度だけイメージを作ります。

```bash
docker build -t expfbook-c docker
```

## 章ごとの対応

### ch01_ieee754 — 第1章「IEEE754の基礎」

```bash
# ビット分解・限界値・ulp・最近接偶数丸め
cd ch01_ieee754 && ../py_tool/.venv/bin/python ieee754_basics.py

# floatのバイナリを実際に覗く実験（導入で使用）
docker run --rm -v "$PWD:/work" -w /work expfbook-c \
    sh ch01_ieee754/run_binary_demo.sh
```

`run_binary_demo.sh` は `write_float.c` / `read_float.c` をビルドして、

1. floatをファイルに書き出し `hexdump -C` で覗く（リトルエンディアンで逆順に見える）
2. 逆に、手で組み立てたバイト列を読ませて意図した値になることを確かめる

という往復を実演します。`hexdump` は Docker イメージの `bsdextrautils` に入っています。

注意点として、指数 e の判定に `Decimal` のべき乗を使うと 2^-126 のように
有効桁が精度設定を超える場合に丸められて誤判定します。
このスクリプトでは必ずビットパターンから厳密に求めています。

### ch02_taylor — 第2章「テーラー展開とその限界」

```bash
cd ch02_taylor
../py_tool/.venv/bin/python remainder_check.py     # 剰余項の検証（2.1節）
../py_tool/.venv/bin/python taylor_limits.py       # 各表のデータ
../py_tool/.venv/bin/python plot_taylor_vs_exp.py  # 図: exp対テーラー近似
../py_tool/.venv/bin/python plot_error_curve.py    # 図: テーラー対ミニマックス
sollya minimax_deg5.sollya                         # 本文に載せているsollyaスクリプト
```

`remainder_check.py` は、ラグランジュの剰余項が主張する
「無限和が1項で書ける」を数値で確かめます。実際の誤差から ξ を逆算し、
本当に 0 と x の間に収まることを確認します。n=0 の場合が平均値の定理に
一致することも見ています。

sollya の `remez(f, n, d, w)` は `||f - p*w||` を最小化する仕様です。
相対誤差 `||(f-p)/f|| = ||1 - p*(1/f)||` を最小化するには
**近似対象を 1、重みを 1/f** として渡す必要があります。

```
p = remez(1, [|0,...,n|], d, 1/f);
```

素直に `remez(f, n, d, 1/f)` と書くと `p ≒ f^2`（= exp(2x)）が返ってきます。

なお sollya はスクリプト末尾に `quit;` が無いと終了コード3を返します。

図の出力先は `figures/02-taylor/` です（環境変数 `EXPF_FIG_DIR` で親ディレクトリを変更できます）。

### ch03_c_numeric — 第3章「C言語における数値表記」

```bash
docker run --rm -v "$PWD:/work" -w /work expfbook-c \
    sh -c "gcc -O2 -std=c11 -o /tmp/a ch03_c_numeric/c_numeric.c -lm && /tmp/a"
```

リテラルの型、16進浮動小数点リテラル、FLT_EVAL_METHOD などを出力します。

### ch04_motivation — 第4章「動機づけ」

```bash
# expf と (float)exp が食い違う入力を全数で数える（数分かかります）
docker run --rm -v "$PWD:/work" -w /work expfbook-c \
    sh -c "gcc -O2 -std=c11 -o /tmp/c ch04_motivation/compare_all.c -lm && /tmp/c"

# 速度比較
docker run --rm -v "$PWD:/work" -w /work expfbook-c \
    sh -c "gcc -O2 -std=c11 -o /tmp/b ch04_motivation/bench_expf.c -lm && /tmp/b"

# double rounding が起きる入力を全数探索（約80秒）
cd ch04_motivation && ../py_tool/.venv/bin/python find_double_rounding.py
```

`find_double_rounding.py` には**陽性対照**が組み込んであります。
「0件でした」という結果は判定ロジックが壊れていても同じように出てしまうため、
人工的に double rounding が起きる値を作って検出できることを毎回確認してから
本探索に入ります。ここが落ちると `assert` で止まります。

探索は2段階です。

1. numpy で全 float32 を走査し、結果が float32 の丸め境界に極端に近いものだけを候補にする
2. 候補だけを mpmath（2進300bit）で厳密に判定する

## 得られた主な結果（第4章時点）

| 項目 | 結果 |
|---|---|
| `expf(x)` と `(float)exp(x)` の食い違い | 42.8億通り中 170,648 個（0.004%）、最大1 ULP |
| double rounding の発生件数 | 22.4億通りを全数探索して **0件** |
| 丸め境界への最接近 | 2^-29 ULP（double rounding に必要な 2^-30 に届かず） |
| 速度比 | `expf` が約1.54倍速い |

