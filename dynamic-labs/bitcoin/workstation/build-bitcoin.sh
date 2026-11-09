#!/bin/bash

set -euo pipefail

mkdir -p /bitcoin && cd /bitcoin 
git clone --depth 1 https://github.com/bitcoin/bitcoin.git
cd bitcoin
git fetch --depth=1 origin 4d7d5f6b79d4c11c47e7a828d81296918fd11d4d
git checkout 4d7d5f6b79d4c11c47e7a828d81296918fd11d4d
git apply /custom-genesis.patch

cmake -B build -S .  -DWITH_QRENCODE=OFF -DBUILD_GUI=OFF \
	CXXFLAGS="-Os -s"  \
	-DBUILD_BITCOIN_QT=OFF \
	-DENABLE_UPNP=OFF \
	-DENABLE_UTILS=ON \
	-DBUILD_BITCOIN_NODE=ON \
	-DCMAKE_EXE_LINKER_FLAGS="-s" \
	-DCMAKE_CXX_FLAGS="-Os -ffunction-sections -fdata-sections -fvisibility=hidden" \
	-DCMAKE_C_FLAGS="-Os -ffunction-sections -fdata-sections -fvisibility=hidden" 
# At most 8 jobs: GCC 14 needs about 1.5 GB a job here, and 20 jobs crashed it on a 16 GB Docker host.
jobs="$(nproc)"; [ "$jobs" -le 8 ] || jobs=8
cmake --build build -j "$jobs" && \
cmake --install build
cd / && rm -r /bitcoin 
