"""Tests for ResourceRequirements and ResourceRequirementsMapper."""

from gb_ai_server.domain import ResourceRequirements, ResourceRequirementsMapper


class TestResourceRequirementsStr:
    def test_formatting(self) -> None:
        req = ResourceRequirements(7, 8, 8192, 999)
        assert str(req) == "7 | 8 | 8192 | 999"


class TestRequirementsForModel:
    def test_7b_model(self) -> None:
        req = ResourceRequirementsMapper.requirements_for_model("qwen-7b.gguf")
        assert req.size_gb == 7
        assert req.vram_needed_gb == 8
        assert req.context_size == 8192

    def test_14b_model(self) -> None:
        req = ResourceRequirementsMapper.requirements_for_model("codellama-14b.gguf")
        assert req.size_gb == 14
        assert req.vram_needed_gb == 10

    def test_24b_model(self) -> None:
        req = ResourceRequirementsMapper.requirements_for_model("qwen-24b.gguf")
        assert req.size_gb == 24
        assert req.vram_needed_gb == 16
        assert req.context_size == 4096

    def test_27b_model(self) -> None:
        req = ResourceRequirementsMapper.requirements_for_model("deepseek-27b.Q4_K_M.gguf")
        assert req.size_gb == 27
        assert req.vram_needed_gb == 16

    def test_unknown_size_uses_default(self) -> None:
        req = ResourceRequirementsMapper.requirements_for_model("unknown-model.gguf")
        assert req.size_gb == 12
        assert req.vram_needed_gb == 12
        assert req.context_size == 4096

    def test_case_insensitive(self) -> None:
        req = ResourceRequirementsMapper.requirements_for_model("QWEN-7B.GGUF")
        assert req.size_gb == 7
