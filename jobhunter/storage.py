import json
from pathlib import Path
from typing import Dict, Any


def load_store(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"roles": {}}
    try:
        with path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"roles": {}}
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return {"roles": {}}


def save_store(path: Path, store: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def diff_dict(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    changed = {}
    keys = set(old.keys()) | set(new.keys())
    for k in keys:
        ov = old.get(k)
        nv = new.get(k)
        if ov != nv:
            changed[k] = {"old": ov, "new": nv}
    return changed


def update_role(store: Dict[str, Any], role_id: str, normalized: Dict[str, Any]) -> Dict[str, Any]:
    roles = store.setdefault("roles", {})
    role = roles.get(role_id)
    if role is None:
        roles[role_id] = {"current": normalized}
        return {"status": "new"}
    if role.get("current") != normalized:
        role["current"] = normalized
        return {"status": "updated"}
    return {"status": "no-change"}
