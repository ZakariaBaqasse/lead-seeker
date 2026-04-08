import yaml
from functools import lru_cache
from pathlib import Path

PROFILE_PATH = Path(__file__).parent.parent / "config" / "profile.yaml"

REQUIRED_KEYS = ["name", "title", "pitch", "projects", "skills"]
REQUIRED_PROJECT_KEYS = ["name", "description", "video_url", "tags"]


def _validate_profile(data: dict) -> None:
    for key in REQUIRED_KEYS:
        if key not in data:
            raise ValueError(f"profile.yaml missing required key: '{key}'")
    if not isinstance(data["projects"], list) or len(data["projects"]) == 0:
        raise ValueError("profile.yaml 'projects' must be a non-empty list")
    for i, project in enumerate(data["projects"]):
        for pkey in REQUIRED_PROJECT_KEYS:
            if pkey not in project:
                raise ValueError(f"profile.yaml projects[{i}] missing required key: '{pkey}'")
    if not isinstance(data["skills"], list) or len(data["skills"]) == 0:
        raise ValueError("profile.yaml 'skills' must be a non-empty list")


@lru_cache(maxsize=1)
def get_profile() -> dict:
    if not PROFILE_PATH.exists():
        raise ValueError(f"profile.yaml not found at {PROFILE_PATH}")
    with open(PROFILE_PATH) as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"profile.yaml is not valid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("profile.yaml must be a YAML mapping")
    _validate_profile(data)
    return data
