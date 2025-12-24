import os
from pathlib import Path


def load_env() -> None:
    """Load .env from project root if present.
    Tries python-dotenv if available; else a minimal parser.
    """
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(dotenv_path=env_path)
        return
    except Exception:
        # Fallback minimal parser
        try:
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            # If even fallback fails, silently ignore
            return
