import subprocess
import argparse
import json
import re
from pathlib import Path
import tomllib


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).parent                  # base-helpers
PYPROJECT = ROOT / "pyproject.toml"
GIT_PACKAGES_JSON = ROOT / "git-packages.json"


# ------------------------------------------------------------
# Regex patterns (line-based, safe)
# ------------------------------------------------------------

GIT_DEP_PATTERN = re.compile(
    r'^(?P<name>[a-zA-Z0-9._-]+)\s*=\s*\{[^}]*git\s*=\s*"[^"]+"[^}]*\}$'
)

PATH_DEP_PATTERN = re.compile(
    r'^(?P<name>[a-zA-Z0-9._-]+)\s*=\s*\{[^}]*path\s*=\s*"[^"]+"[^}]*\}$'
)


# ------------------------------------------------------------
# Loaders
# ------------------------------------------------------------

def load_pyproject():
    with PYPROJECT.open("rb") as f:
        return tomllib.load(f)


def load_pyproject_text():
    return PYPROJECT.read_text()


def load_git_packages():
    if not GIT_PACKAGES_JSON.exists():
        raise RuntimeError("git-packages.json not found")
    return json.loads(GIT_PACKAGES_JSON.read_text())


# ------------------------------------------------------------
# Git helpers
# ------------------------------------------------------------

def get_latest_commit(local_repo: Path, git_url: str) -> str:
    """
    Prefer local repo HEAD.
    Fallback to remote HEAD if local repo is missing.
    """
    if local_repo.exists() and (local_repo / ".git").exists():
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=local_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    # Fallback: remote HEAD
    result = subprocess.run(
        ["git", "ls-remote", git_url, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["git", "local"],
        default="git",
        help="git = force git deps, local = force path deps"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for updates without modifying pyproject.toml"
    )
    args = parser.parse_args()

    pyproject = load_pyproject()
    pyproject_text = load_pyproject_text()
    git_packages = load_git_packages()

    if "tool" not in pyproject or "poetry" not in pyproject["tool"]:
        raise RuntimeError("tool.poetry section not found in pyproject.toml")

    updates = {}

    for pkg, cfg in git_packages.items():
        local_path = (ROOT / cfg["local_path"]).resolve()
        git_url = cfg["git_path"]

        if not local_path.exists():
            print(f"⚠ {pkg}: local path missing ({local_path})")

        commit = get_latest_commit(local_path, git_url) if args.mode == "git" else None

        for line in pyproject_text.splitlines():
            stripped = line.strip()

            # --- PATH dependency ---
            if PATH_DEP_PATTERN.match(stripped) and stripped.startswith(pkg):
                if args.mode == "git":
                    new_line = f'{pkg} = {{ git = "{git_url}", rev = "{commit}" }}'
                    updates[line] = new_line
                    print(f"→ {pkg}: local → git @ rev={commit}")
                break

            # --- GIT dependency ---
            if GIT_DEP_PATTERN.match(stripped) and stripped.startswith(pkg):
                if args.mode == "git":
                    new_line = f'{pkg} = {{ git = "{git_url}", rev = "{commit}" }}'
                    if line.strip() != new_line.strip():
                        updates[line] = new_line
                        if args.dry_run:
                            print(f"→ {pkg}: would update to rev={commit}")

                elif args.mode == "local":
                    new_line = f'{pkg} = {{ path = "{cfg["local_path"]}", develop = true }}'
                    if line.strip() != new_line.strip():
                        updates[line] = new_line
                        if args.dry_run:
                            print(f"→ {pkg}: would update")
                break

    # ------------------------------------------------------------
    # Apply updates
    # ------------------------------------------------------------

    if updates:
        if args.dry_run:
            print("\n⚠ Updates would be applied, but --dry-run enabled")
            for old, new in updates.items():
                print(f"- {old}")
                print(f"+ {new}\n")
            # Exit non-zero to signal pre-push hook failure
            exit(1)
        else:
            updated_text = pyproject_text
            for old, new in updates.items():
                updated_text = updated_text.replace(old, new)
            PYPROJECT.write_text(updated_text)
            print("\npyproject.toml updated successfully")
    else:
        print("\nNo changes required")
        exit(0)


if __name__ == "__main__":
    main()
