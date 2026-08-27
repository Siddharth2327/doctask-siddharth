from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromptDefinition:
    name: str
    version: str
    content: str


class PromptNotFoundError(FileNotFoundError):
    """Raised when a requested prompt version does not exist."""


class PromptManager:
    """Loads version-controlled Docsnary prompts."""

    def __init__(self, prompts_root: Path | None = None) -> None:
        if prompts_root is None:
            prompts_root = (
                Path(__file__).resolve().parents[4] / "prompts"
            )

        self.prompts_root = prompts_root

    def get(
        self,
        name: str,
        version: str = "v1",
    ) -> PromptDefinition:
        path = self.prompts_root / name / f"{version}.txt"

        if not path.is_file():
            raise PromptNotFoundError(
                f"Prompt '{name}' version '{version}' was not found"
            )

        return PromptDefinition(
            name=name,
            version=version,
            content=path.read_text(encoding="utf-8"),
        )


def build_prompt_metadata(
    prompt: PromptDefinition,
    *,
    model: str,
    model_version: str | None = None,
) -> dict[str, Any]:
    return {
        "prompt_name": prompt.name,
        "prompt_version": prompt.version,
        "model": model,
        "model_version": model_version,
    }