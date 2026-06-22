# Adding a Model

Two files need editing to add a new model:

- `scripts/models.conf.sh` — declares the model so the download pipeline knows about it
- `docker-compose.yml` — adds a container to serve it

---

## 1. `scripts/models.conf.sh`

One pipe-delimited entry per model:

```
"display_name|filename.gguf|download_url"
```

Example:

```bash
MODELS=(
  "qwen2.5-coder:7b|qwen2.5-coder-7b-instruct-q4_k_m.gguf|https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
)
```

- **display_name** — human-readable identifier (used for container naming, logging, etc.)
- **filename** — the GGUF file name (must match the last path segment of the URL)
- **url** — direct HuggingFace resolve URL to the GGUF file

The URL pattern is:

```
https://huggingface.co/<org>/<repo>/resolve/main/<file>.gguf
```

---

## 2. `docker-compose.yml`

Add a new service entry. Follow the existing pattern:

```yaml
  llama-<shortname>:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    container_name: llama-<shortname>
    profiles:
      - extra
    restart: unless-stopped
    devices:
      - nvidia.com/gpu=all
    security_opt:
      - label=disable
    ports:
      - "<port>:8080"
    volumes:
      - llama_models:/models
    command:
      - --model
      - /models/<filename>.gguf
      - --host
      - 0.0.0.0
      - --port
      - "8080"
      - --n-gpu-layers
      - "<layers>"
      - --ctx-size
      - "<context>"
    networks:
      - ai-net
```

### Naming conventions

- **service name** — `llama-<shortname>` (lowercase, hyphens)
- **container_name** — `llama-<shortname>` (must match what tools reference)
- **port** — unique host port starting from 8081 (increment for each model: 8081, 8082, 8083...)
- **n-gpu-layers** — `"999"` to offload all layers to GPU, or a lower number for smaller GPUs
- **ctx-size** — `"8192"` is typical; large models may need less, small models can handle more
- **profiles** — `- extra` keeps the service out of the default `up` (only started with `up-all`)

---

## 3. Bootstrap

After editing both files, run:

```bash
make bootstrap         # full pipeline
make bootstrap-dry     # preview only
make bootstrap-quick   # skip download & health checks
```

The Python bootstrap pipeline handles:

1. Parsing `scripts/models.conf.sh` into `ModelEntry` objects
2. Downloading each GGUF file via `huggingface_hub` (with `HF_TOKEN` for gated repos)
3. Starting containers (`podman-compose up -d`)
4. Copying `.gguf` files into the `llama_models` volume at `/models/`
5. Restarting the primary `llama-coder` container
6. Polling `http://localhost:8081/health` until ready

---

## Notes

### Single-file vs multi-file GGUFs

The current infrastructure only supports single-file GGUFs. Large models (200GB+) are often distributed as split/multi-file GGUFs (e.g., `model-00001-of-00007.gguf` through `model-00007-of-00007.gguf`). These require changes to:

- `model_downloader.py` — use `snapshot_download` with `allow_patterns` to fetch all split files instead of `hf_hub_download` for a single file
- `model_copier_service.py` — copy subdirectory structures into the container, not just a flat file
- `docker-compose.yml` — `--model` path must point to the first split file in its subdirectory

### Port allocation

Ports start at 8081 (the primary `llama-coder`). Each additional model gets the next port. The `PortAllocator` domain class maps model index → port via `BASE_PORT + index`.

### Model volume

All models live in the `llama_models` Docker volume mounted at `/models/` in every container. Downloaded GGUF files are copied into this volume by the `ModelCopierService`.

### Gated repositories

Models requiring authentication need `--hf-token` passed to the bootstrap command, or `HF_TOKEN` set in `.env`.
