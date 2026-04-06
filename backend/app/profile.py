import os
from functools import lru_cache

import yaml

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "profile.yaml")


def _validate_profile(data: dict) -> None:
    """Validate required profile fields. Raises ValueError with descriptive message."""
    required_str_fields = ["name", "title", "pitch"]
    for field in required_str_fields:
        if field not in data or not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"profile.yaml: '{field}' is required and must be a non-empty string")

    if "projects" not in data or not isinstance(data["projects"], list) or len(data["projects"]) == 0:
        raise ValueError("profile.yaml: 'projects' is required and must be a non-empty list")

    for i, project in enumerate(data["projects"]):
        for pfield in ["name", "description", "video_url", "tags"]:
            if pfield not in project:
                raise ValueError(f"profile.yaml: projects[{i}] is missing required field '{pfield}'")
        if not isinstance(project["tags"], list):
            raise ValueError(f"profile.yaml: projects[{i}].tags must be a list")

    if "skills" not in data or not isinstance(data["skills"], list):
        raise ValueError("profile.yaml: 'skills' is required and must be a list of strings")


@lru_cache(maxsize=1)
def get_profile() -> dict:
    """Load and cache the freelancer profile from config/profile.yaml."""
    path = os.path.abspath(PROFILE_PATH)
    if not os.path.exists(path):
        raise ValueError(f"profile.yaml not found at {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("profile.yaml: must be a YAML mapping at the top level")
    _validate_profile(data)
    return data
