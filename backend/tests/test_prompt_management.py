from pathlib import Path

import pytest

from app.integrations.ai.prompts import (
    PromptManager,
    PromptNotFoundError,
    build_prompt_metadata,
)


def test_classification_prompt_is_loaded():
    manager = PromptManager()

    prompt = manager.get("classification", "v1")

    assert prompt.name == "classification"
    assert prompt.version == "v1"
    assert prompt.content.strip()


def test_all_required_prompts_are_versioned():
    manager = PromptManager()

    prompt_names = [
        "classification",
        "extraction",
        "conflict_detection",
        "validation",
        "reporting",
    ]

    for name in prompt_names:
        prompt = manager.get(name, "v1")

        assert prompt.name == name
        assert prompt.version == "v1"
        assert prompt.content.strip()


def test_prompt_metadata_contains_required_run_information():
    manager = PromptManager()

    prompt = manager.get("extraction", "v1")

    metadata = build_prompt_metadata(
        prompt,
        model="mock-model",
        model_version="mock-v1",
    )

    assert metadata == {
        "prompt_name": "extraction",
        "prompt_version": "v1",
        "model": "mock-model",
        "model_version": "mock-v1",
    }


def test_model_version_can_be_unknown():
    manager = PromptManager()

    prompt = manager.get("classification", "v1")

    metadata = build_prompt_metadata(
        prompt,
        model="mock-model",
    )

    assert metadata["model"] == "mock-model"
    assert metadata["model_version"] is None


def test_missing_prompt_version_raises():
    manager = PromptManager()

    with pytest.raises(PromptNotFoundError):
        manager.get("extraction", "v999")


def test_missing_prompt_name_raises():
    manager = PromptManager()

    with pytest.raises(PromptNotFoundError):
        manager.get("does_not_exist", "v1")


def test_prompt_manager_can_use_custom_root(tmp_path: Path):
    prompt_dir = tmp_path / "custom"
    prompt_dir.mkdir()

    prompt_file = prompt_dir / "v1.txt"
    prompt_file.write_text(
        "custom prompt",
        encoding="utf-8",
    )

    manager = PromptManager(tmp_path)

    prompt = manager.get("custom", "v1")

    assert prompt.content == "custom prompt"