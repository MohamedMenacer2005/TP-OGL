"""
Prompt manager for loading and formatting agent prompts.
Prompts are stored externally to allow versioning and dynamic injection.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict


_PROMPTS_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompts.json"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


@lru_cache(maxsize=4)
def _load_prompts(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class PromptManager:
    """
    Loads prompts from a JSON file and formats them with runtime context.
    """

    def __init__(self, prompts_path: str | None = None) -> None:
        self.prompts_path = str(prompts_path or _PROMPTS_PATH)

    def get(self, name: str) -> str:
        prompts = _load_prompts(self.prompts_path)
        if name not in prompts:
            raise KeyError(f"Prompt '{name}' not found in {self.prompts_path}")
        return prompts[name]

    def format(self, name: str, **kwargs: str) -> str:
        template = self.get(name)
        return template.format_map(_SafeDict(kwargs))
