# 本書のC言語側の検証環境。
# glibcのlibmの挙動を見たいので、musl系(alpine)ではなくdebian(glibc)を使う。
FROM debian:bookworm-slim

# bsdextrautils は hexdump(1) のため（第1章でバイナリを覗くのに使う）
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libc6-dev libmpfr-dev bsdextrautils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
