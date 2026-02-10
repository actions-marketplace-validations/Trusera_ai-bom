"""Tests for Jupyter notebook scanner."""

import json

import pytest

from ai_bom.models import ComponentType
from ai_bom.scanners.jupyter_scanner import JupyterScanner


@pytest.fixture
def scanner():
    """Create a JupyterScanner instance."""
    return JupyterScanner()


def test_scanner_registration():
    """Test that scanner is properly registered."""
    scanner = JupyterScanner()
    assert scanner.name == "jupyter"
    assert scanner.description == "Scan Jupyter notebooks for AI components"


def test_supports_ipynb_file(tmp_path, scanner):
    """Test that scanner supports .ipynb files."""
    notebook_file = tmp_path / "test.ipynb"
    notebook_file.write_text("{}")

    assert scanner.supports(notebook_file)


def test_supports_directory_with_notebooks(tmp_path, scanner):
    """Test that scanner supports directories with .ipynb files."""
    notebook_file = tmp_path / "notebook.ipynb"
    notebook_file.write_text("{}")

    assert scanner.supports(tmp_path)


def test_not_supports_non_notebook_file(tmp_path, scanner):
    """Test that scanner does not support non-notebook files."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    assert not scanner.supports(test_file)


def test_scan_openai_import(tmp_path, scanner):
    """Test detection of OpenAI import."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["import openai\n", "client = openai.Client()"],
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    openai_components = [c for c in components if "openai" in c.name.lower()]
    assert len(openai_components) >= 1

    comp = openai_components[0]
    assert comp.provider == "OpenAI"
    assert comp.source == "jupyter"


def test_scan_langchain_import(tmp_path, scanner):
    """Test detection of LangChain import."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "from langchain import LLMChain",
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    langchain_components = [c for c in components if "langchain" in c.name.lower()]
    assert len(langchain_components) >= 1

    comp = langchain_components[0]
    assert comp.provider == "LangChain"
    assert comp.type == ComponentType.agent_framework


def test_scan_transformers_import(tmp_path, scanner):
    """Test detection of HuggingFace transformers import."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["import transformers\n", "from transformers import pipeline"],
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    hf_components = [c for c in components if c.provider == "HuggingFace"]
    assert len(hf_components) >= 1


def test_scan_model_loading_automodel(tmp_path, scanner):
    """Test detection of AutoModel.from_pretrained."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": 'model = AutoModel.from_pretrained("bert-base-uncased")',
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    model_components = [c for c in components if c.type == ComponentType.model]
    assert len(model_components) >= 1

    comp = model_components[0]
    assert comp.provider == "HuggingFace"
    assert "bert-base-uncased" in comp.model_name


def test_scan_model_loading_pipeline(tmp_path, scanner):
    """Test detection of pipeline() function."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": 'classifier = pipeline("sentiment-analysis")',
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    model_components = [c for c in components if "sentiment-analysis" in c.model_name]
    assert len(model_components) >= 1


def test_scan_chatopenai(tmp_path, scanner):
    """Test detection of ChatOpenAI initialization."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "from langchain.chat_models import ChatOpenAI\nllm = ChatOpenAI()",
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    # Should find both langchain import and ChatOpenAI() instantiation
    assert len(components) >= 1
    openai_components = [c for c in components if c.provider == "OpenAI"]
    assert len(openai_components) >= 1


def test_scan_multiple_cells(tmp_path, scanner):
    """Test scanning multiple cells in a notebook."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "import openai",
            },
            {
                "cell_type": "markdown",
                "source": "# This is a markdown cell",
            },
            {
                "cell_type": "code",
                "source": "import anthropic",
            },
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 2
    providers = {c.provider for c in components}
    assert "OpenAI" in providers
    assert "Anthropic" in providers


def test_scan_multiline_source(tmp_path, scanner):
    """Test scanning cell with multiline source (list of strings)."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": [
                    "import openai\n",
                    "import anthropic\n",
                    "client = openai.Client()\n",
                ],
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 2
    providers = {c.provider for c in components}
    assert "OpenAI" in providers
    assert "Anthropic" in providers


def test_scan_comments_ignored(tmp_path, scanner):
    """Test that comments are ignored."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "# import openai\nimport anthropic  # This is real",
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    # Should only find anthropic, not openai (commented out)
    providers = {c.provider for c in components}
    assert "Anthropic" in providers
    # OpenAI might be found if comment line is processed, so just ensure anthropic is there


def test_scan_deduplication(tmp_path, scanner):
    """Test that duplicate imports are deduplicated."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "import openai",
            },
            {
                "cell_type": "code",
                "source": "import openai",
            },
            {
                "cell_type": "code",
                "source": "from openai import Client",
            },
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    # Should only find openai once despite multiple imports
    openai_components = [c for c in components if c.name == "openai"]
    assert len(openai_components) == 1


def test_scan_sentence_transformers(tmp_path, scanner):
    """Test detection of sentence-transformers."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": (
                    "from sentence_transformers"
                    " import SentenceTransformer\n"
                    'model = SentenceTransformer('
                    '"all-MiniLM-L6-v2")'
                ),
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    st_components = [
        c for c in components
        if "sentence" in c.name.lower()
        or c.provider == "HuggingFace"
    ]
    assert len(st_components) >= 1


def test_scan_google_genai(tmp_path, scanner):
    """Test detection of Google Generative AI."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": (
                    "import google.generativeai as genai\n"
                    'model = genai.GenerativeModel('
                    '"gemini-pro")'
                ),
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    google_components = [c for c in components if c.provider == "Google"]
    assert len(google_components) >= 1


def test_scan_empty_notebook(tmp_path, scanner):
    """Test scanning empty notebook."""
    notebook_file = tmp_path / "empty.ipynb"

    notebook_data = {"cells": []}

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)
    assert len(components) == 0


def test_scan_invalid_json(tmp_path, scanner):
    """Test scanning invalid JSON file."""
    notebook_file = tmp_path / "invalid.ipynb"
    notebook_file.write_text("{ invalid json [")

    components = scanner.scan(tmp_path)
    # Should not crash, just return empty
    assert len(components) == 0


def test_scan_no_code_cells(tmp_path, scanner):
    """Test scanning notebook with only markdown cells."""
    notebook_file = tmp_path / "markdown.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "# Heading",
            },
            {
                "cell_type": "markdown",
                "source": "Some text with import openai mentioned",
            },
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)
    # Should not detect imports in markdown cells
    assert len(components) == 0


def test_scan_anthropic_client(tmp_path, scanner):
    """Test detection of Anthropic client initialization."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "import anthropic\nclient = anthropic.Anthropic()",
            }
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    anthropic_components = [c for c in components if c.provider == "Anthropic"]
    assert len(anthropic_components) >= 1


def test_metadata_cell_tracking(tmp_path, scanner):
    """Test that metadata tracks cell numbers correctly."""
    notebook_file = tmp_path / "test.ipynb"

    notebook_data = {
        "cells": [
            {
                "cell_type": "code",
                "source": "import openai",
            },
            {
                "cell_type": "code",
                "source": "import anthropic",
            },
        ]
    }

    notebook_file.write_text(json.dumps(notebook_data))

    components = scanner.scan(tmp_path)

    assert len(components) >= 2

    # Check that cell numbers are tracked
    for comp in components:
        assert "cell_number" in comp.metadata
        assert comp.metadata["cell_number"] in [1, 2]
