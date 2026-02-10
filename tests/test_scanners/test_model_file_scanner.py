"""Tests for model file scanner."""


import pytest

from ai_bom.models import ComponentType
from ai_bom.scanners.model_file_scanner import ModelFileScanner


@pytest.fixture
def scanner():
    """Create a ModelFileScanner instance."""
    return ModelFileScanner()


def test_scanner_registration():
    """Test that scanner is properly registered."""
    scanner = ModelFileScanner()
    assert scanner.name == "model-files"
    assert scanner.description == "Detect AI model binary files"


def test_supports_onnx_file(tmp_path, scanner):
    """Test that scanner supports .onnx files."""
    model_file = tmp_path / "model.onnx"
    model_file.write_bytes(b"fake onnx content")

    assert scanner.supports(model_file)


def test_supports_pytorch_file(tmp_path, scanner):
    """Test that scanner supports .pt and .pth files."""
    pt_file = tmp_path / "model.pt"
    pt_file.write_bytes(b"fake pytorch content")

    pth_file = tmp_path / "weights.pth"
    pth_file.write_bytes(b"fake pytorch content")

    assert scanner.supports(pt_file)
    assert scanner.supports(pth_file)


def test_supports_tensorflow_file(tmp_path, scanner):
    """Test that scanner supports .pb files."""
    model_file = tmp_path / "model.pb"
    model_file.write_bytes(b"fake tensorflow content")

    assert scanner.supports(model_file)


def test_supports_safetensors_file(tmp_path, scanner):
    """Test that scanner supports .safetensors files."""
    model_file = tmp_path / "model.safetensors"
    model_file.write_bytes(b"fake safetensors content")

    assert scanner.supports(model_file)


def test_supports_gguf_file(tmp_path, scanner):
    """Test that scanner supports .gguf files."""
    model_file = tmp_path / "model.gguf"
    model_file.write_bytes(b"fake gguf content")

    assert scanner.supports(model_file)


def test_supports_large_bin_file(tmp_path, scanner):
    """Test that scanner supports large .bin files (>1MB)."""
    model_file = tmp_path / "model.bin"
    # Create a file larger than 1MB
    model_file.write_bytes(b"0" * (2 * 1024 * 1024))  # 2MB

    assert scanner.supports(model_file)


def test_not_supports_small_bin_file(tmp_path, scanner):
    """Test that scanner does not support small .bin files (<1MB)."""
    small_file = tmp_path / "config.bin"
    small_file.write_bytes(b"small content")

    assert not scanner.supports(small_file)


def test_not_supports_non_model_file(tmp_path, scanner):
    """Test that scanner does not support non-model files."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    assert not scanner.supports(test_file)


def test_scan_onnx_model(tmp_path, scanner):
    """Test scanning an ONNX model file."""
    model_file = tmp_path / "resnet50.onnx"
    model_file.write_bytes(b"fake onnx model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.type == ComponentType.model
    assert comp.name == "resnet50.onnx"
    assert comp.metadata["format"] == "ONNX"
    assert comp.metadata["extension"] == ".onnx"
    assert "file_size_bytes" in comp.metadata
    assert "file_size_mb" in comp.metadata
    assert comp.source == "model-file"


def test_scan_pytorch_model(tmp_path, scanner):
    """Test scanning a PyTorch model file."""
    model_file = tmp_path / "bert.pt"
    model_file.write_bytes(b"fake pytorch model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.type == ComponentType.model
    assert comp.metadata["format"] == "PyTorch"
    assert comp.provider == "PyTorch"


def test_scan_tensorflow_model(tmp_path, scanner):
    """Test scanning a TensorFlow model file."""
    model_file = tmp_path / "model.pb"
    model_file.write_bytes(b"fake tf model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "TensorFlow"
    assert comp.provider == "TensorFlow"


def test_scan_safetensors_model(tmp_path, scanner):
    """Test scanning a Safetensors model file."""
    model_file = tmp_path / "model.safetensors"
    model_file.write_bytes(b"fake safetensors" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "Safetensors"
    assert comp.provider == "HuggingFace"


def test_scan_gguf_model(tmp_path, scanner):
    """Test scanning a GGUF model file."""
    model_file = tmp_path / "llama-7b.gguf"
    model_file.write_bytes(b"fake gguf model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "GGUF"
    assert comp.provider == "llama.cpp"


def test_scan_large_bin_model(tmp_path, scanner):
    """Test scanning a large .bin file."""
    model_file = tmp_path / "pytorch_model.bin"
    # Create 2MB file
    model_file.write_bytes(b"0" * (2 * 1024 * 1024))

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "Binary Model Weights"
    assert comp.metadata["file_size_mb"] == 2.0


def test_scan_multiple_models(tmp_path, scanner):
    """Test scanning directory with multiple model files."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    (models_dir / "model1.onnx").write_bytes(b"model1" * 1000)
    (models_dir / "model2.pt").write_bytes(b"model2" * 1000)
    (models_dir / "model3.safetensors").write_bytes(b"model3" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 3
    formats = {c.metadata["format"] for c in components}
    assert "ONNX" in formats
    assert "PyTorch" in formats
    assert "Safetensors" in formats


def test_scan_nested_directories(tmp_path, scanner):
    """Test scanning nested directories for models."""
    nested_dir = tmp_path / "models" / "subdir" / "weights"
    nested_dir.mkdir(parents=True)

    model_file = nested_dir / "model.onnx"
    model_file.write_bytes(b"nested model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert "weights" in comp.location.file_path


def test_scan_large_model_flag(tmp_path, scanner):
    """Test that large models (>1GB) are flagged."""
    model_file = tmp_path / "large_model.onnx"
    # Create 1.1GB file
    model_file.write_bytes(b"0" * (1100 * 1024 * 1024))

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert "large_model_file" in comp.flags


def test_scan_small_model_no_flag(tmp_path, scanner):
    """Test that small models are not flagged."""
    model_file = tmp_path / "small_model.onnx"
    model_file.write_bytes(b"small" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert "large_model_file" not in comp.flags


def test_guess_provider_huggingface(tmp_path, scanner):
    """Test provider guessing for HuggingFace paths."""
    hf_dir = tmp_path / "huggingface" / "models"
    hf_dir.mkdir(parents=True)

    model_file = hf_dir / "model.bin"
    model_file.write_bytes(b"0" * (2 * 1024 * 1024))

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.provider == "HuggingFace"


def test_guess_provider_llama(tmp_path, scanner):
    """Test provider guessing for llama paths."""
    llama_dir = tmp_path / "llama" / "models"
    llama_dir.mkdir(parents=True)

    model_file = llama_dir / "model.bin"
    model_file.write_bytes(b"0" * (2 * 1024 * 1024))

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.provider == "llama.cpp"


def test_scan_tflite_model(tmp_path, scanner):
    """Test scanning TensorFlow Lite model."""
    model_file = tmp_path / "model.tflite"
    model_file.write_bytes(b"tflite model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "TensorFlow Lite"


def test_scan_mlmodel_file(tmp_path, scanner):
    """Test scanning Core ML model."""
    model_file = tmp_path / "model.mlmodel"
    model_file.write_bytes(b"mlmodel" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "Core ML"
    assert comp.provider == "Apple Core ML"


def test_scan_ggml_file(tmp_path, scanner):
    """Test scanning GGML model file."""
    model_file = tmp_path / "model.ggml"
    model_file.write_bytes(b"ggml model" * 1000)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["format"] == "GGML"
    assert comp.provider == "llama.cpp"


def test_scan_single_file_path(tmp_path, scanner):
    """Test scanning a single file path directly."""
    model_file = tmp_path / "model.onnx"
    model_file.write_bytes(b"onnx model" * 1000)

    components = scanner.scan(model_file)

    assert len(components) == 1
    comp = components[0]
    assert comp.name == "model.onnx"


def test_scan_empty_directory(tmp_path, scanner):
    """Test scanning empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    components = scanner.scan(tmp_path)
    assert len(components) == 0


def test_file_size_calculation(tmp_path, scanner):
    """Test that file sizes are calculated correctly."""
    model_file = tmp_path / "model.onnx"
    # Create 5MB file
    file_size = 5 * 1024 * 1024
    model_file.write_bytes(b"0" * file_size)

    components = scanner.scan(tmp_path)

    assert len(components) == 1
    comp = components[0]
    assert comp.metadata["file_size_bytes"] == file_size
    assert comp.metadata["file_size_mb"] == 5.0
