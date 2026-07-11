"""Lightweight GGUF metadata reader — extracts context window from GGUF files."""

from __future__ import annotations

import struct
from pathlib import Path

# GGUF value types
_GGUF_TYPE_UINT32 = 4
_GGUF_TYPE_INT32 = 5
_GGUF_TYPE_UINT64 = 10
_GGUF_TYPE_INT64 = 11

# Keys that contain the context window size (tried in order)
_CONTEXT_KEYS = [
    "llama.context_length",
    "llama.rope.context_length",
    "llama.context_length_kv",
    "tokenizer.ggml.context_length",
    "llama.attention.context_length",
]


def read_context_window(gguf_path: Path | str) -> int | None:
    """Read the context window from a GGUF file header.

    Opens the file, reads GGUF header metadata, and extracts the
    context length from known metadata keys.

    Returns the context window as an int, or None if not found.
    """
    path = Path(gguf_path)
    if not path.exists() or path.stat().st_size < 32:
        return None

    try:
        with open(path, "rb") as f:
            # Magic
            magic = f.read(4)
            if magic != b"GGUF":
                return None

            # Version
            version_raw = f.read(4)
            version = struct.unpack("<I", version_raw)[0]
            if version not in (2, 3):
                return None

            # Skip tensor_count (8 bytes)
            f.read(8)

            # Metadata KV count
            kv_count_raw = f.read(8)
            kv_count = struct.unpack("<Q", kv_count_raw)[0]

            for _ in range(kv_count):
                # Key: uint64 length + string
                key_len_raw = f.read(8)
                if len(key_len_raw) < 8:
                    break
                key_len = struct.unpack("<Q", key_len_raw)[0]
                key = f.read(key_len).decode("utf-8", errors="replace")

                # Value type
                type_raw = f.read(4)
                if len(type_raw) < 4:
                    break
                value_type = struct.unpack("<I", type_raw)[0]

                # Value
                value = _read_gguf_value(f, value_type, version)

                if key.lower().endswith("context_length") or key.lower().endswith("ctx_length"):
                    if isinstance(value, int) and value > 0:
                        return value

                # Also check known keys
                for ck in _CONTEXT_KEYS:
                    if key == ck and isinstance(value, int) and value > 0:
                        return value

    except (OSError, struct.error, UnicodeDecodeError):
        pass

    return None


def kv_cache_mb_per_token(filename: str) -> float | None:
    """Estimate KV cache memory per token from GGUF metadata.

    KV cache = 2 × n_layers × n_embd × sizeof(fp16)
    Divided by quantization factor if KV cache is quantized.

    Returns MB per token, or None if GGUF can't be read.
    """
    ctx = _read_gguf_kv(filename, {
        ".block_count": "block_count",
        ".embedding_length": "embedding_length",
        ".attention.head_count_kv": "n_kv_heads",
        ".attention.head_count": "n_heads",
    })
    if not ctx:
        return None

    n_layers = ctx.get("block_count", 0)
    n_embd = ctx.get("embedding_length", 0)
    n_kv_heads = ctx.get("n_kv_heads") or ctx.get("n_heads", 0)

    if not n_layers or not n_embd:
        return None

    # KV cache = 2 * n_layers * n_kv_heads * head_dim * 2 bytes (fp16)
    # where head_dim = n_embd / n_heads
    head_dim = n_embd // n_kv_heads if n_kv_heads else 128
    bytes_per_token = 2 * n_layers * n_kv_heads * head_dim * 2  # fp16

    return bytes_per_token / (1024 * 1024)


def _read_gguf_kv(path: str, keys: dict[str, str]) -> dict[str, int]:
    """Read specific GGUF metadata keys and return a dict of {short_name: value}."""
    import os
    import struct

    result: dict[str, int] = {}
    if not os.path.exists(path):
        return result

    reverse = {v: k for k, v in keys.items()}

    # Build suffix matcher: check if any key ends with the full GGUF key
    suffixes = [(k, short) for k, short in keys.items()]

    try:
        with open(path, "rb") as f:
            if f.read(4) != b"GGUF":
                return result
            version = struct.unpack("<I", f.read(4))[0]
            if version not in (2, 3):
                return result
            f.read(8)  # tensor_count
            kv_count = struct.unpack("<Q", f.read(8))[0]

            for _ in range(kv_count):
                key_len = struct.unpack("<Q", f.read(8))[0]
                key = f.read(key_len).decode("utf-8", errors="replace")
                value_type = struct.unpack("<I", f.read(4))[0]

                # Match by exact key or by suffix
                matched_short = reverse.get(key)
                if not matched_short:
                    for full_key, short in suffixes:
                        if key.endswith(full_key):
                            matched_short = short
                            break

                if matched_short:
                    if value_type in (4, 5):  # uint32, int32
                        result[matched_short] = struct.unpack("<I", f.read(4))[0]
                    elif value_type in (10, 11):  # uint64, int64
                        result[matched_short] = struct.unpack("<Q", f.read(8))[0]
                    elif value_type == 0:
                        result[matched_short] = f.read(1)[0]
                    else:
                        _skip_gguf_value(f, value_type)
                else:
                    _skip_gguf_value(f, value_type)
    except (OSError, struct.error):
        pass

    return result


def _skip_gguf_value(f, value_type: int) -> None:
    """Skip over a GGUF value without reading it."""
    import struct
    if value_type in (0, 1, 7):
        f.read(1)
    elif value_type in (2, 3):
        f.read(2)
    elif value_type in (4, 5):
        f.read(4)
    elif value_type == 6:
        f.read(4)
    elif value_type == 8:
        slen = struct.unpack("<Q", f.read(8))[0]
        f.read(slen)
    elif value_type == 9:
        arr_type = struct.unpack("<I", f.read(4))[0]
        arr_count = struct.unpack("<Q", f.read(8))[0]
        for _ in range(arr_count):
            _skip_gguf_value(f, arr_type)
    elif value_type in (10, 11):
        f.read(8)
    elif value_type == 12:
        f.read(8)


def _read_gguf_value(f, value_type: int, version: int) -> int | float | str | bool | None:
    """Read a single GGUF value based on its type."""
    if value_type == 0:   # uint8
        raw = f.read(1)
        return raw[0] if raw else None
    elif value_type == 1:  # int8
        raw = f.read(1)
        return struct.unpack("<b", raw)[0] if raw else None
    elif value_type == 2:  # uint16
        return struct.unpack("<H", f.read(2))[0]
    elif value_type == 3:  # int16
        return struct.unpack("<h", f.read(2))[0]
    elif value_type == 4:  # uint32
        return struct.unpack("<I", f.read(4))[0]
    elif value_type == 5:  # int32
        return struct.unpack("<i", f.read(4))[0]
    elif value_type == 6:  # float32
        return struct.unpack("<f", f.read(4))[0]
    elif value_type == 7:  # bool
        return f.read(1)[0] != 0
    elif value_type == 8:  # string
        str_len = struct.unpack("<Q", f.read(8))[0]
        return f.read(str_len).decode("utf-8", errors="replace")
    elif value_type == 9:  # array
        # Array: type + count + values
        arr_type = struct.unpack("<I", f.read(4))[0]
        arr_count = struct.unpack("<Q", f.read(8))[0]
        for _ in range(arr_count):
            _read_gguf_value(f, arr_type, version)
        return None
    elif value_type == 10:  # uint64
        return struct.unpack("<Q", f.read(8))[0]
    elif value_type == 11:  # int64
        return struct.unpack("<q", f.read(8))[0]
    elif value_type == 12:  # float64
        return struct.unpack("<d", f.read(8))[0]
    else:
        return None
