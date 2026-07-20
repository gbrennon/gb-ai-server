FROM docker.io/nvidia/cuda:12.4.0-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y \
    git cmake build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ggml-org/llama.cpp /build && \
    cd /build && \
    cmake -B build -DLLAMA_CUDA=ON -DLLAMA_NATIVE=OFF && \
    cmake --build build --config Release -j $(nproc) --target llama-server

FROM docker.io/nvidia/cuda:12.4.0-runtime-ubuntu22.04

COPY --from=builder /build/build/bin/llama-server /app/llama-server

EXPOSE 8080

ENTRYPOINT ["/app/llama-server"]
