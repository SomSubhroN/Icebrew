
#!/usr/bin/env bash

set -euo pipefail

# --------------------------------------------------
# Icebrew Repository Scaffold
# Reproducible, idempotent project structure creation
# --------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR"

directories=(
    "src/icebrew/cli/commands"
    "src/icebrew/core"
    "src/icebrew/configuration"
    "src/icebrew/data"
    "src/icebrew/stats"
    "src/icebrew/plotting"
    "src/icebrew/sentiment"
    "src/icebrew/insight"
    "src/icebrew/ai/backends"
    "src/icebrew/ai/inference"
    "src/icebrew/ai/benchmarks"
    "src/icebrew/models"
    "src/icebrew/media/image"
    "src/icebrew/media/video"
    "src/icebrew/media/analysis"
    "src/icebrew/media/backends"
    "src/icebrew/reporting"
    "src/icebrew/experiments"
    "src/icebrew/diagnostics/checks"
    "src/icebrew/extensions"
    "src/icebrew/security"
    "src/icebrew/utils"
    "catalog/models"
    "catalog/backends"
    "config/schemas"
    "docs"
    "tests/unit"
    "tests/integration"
    "tests/cli"
    "tests/diagnostics"
    "tests/media"
    "tests/ai"
    "tests/installers"
    "scripts/development"
    "scripts/testing"
    "scripts/maintenance"
    "scripts/release"
    "packaging/bootstrap"
    "packaging/launchers"
    "packaging/runtime"
    "packaging/uninstall"
    "examples"
    "benchmarks"
    ".github/workflows"
    ".github/ISSUE_TEMPLATE"
)

files=(
    "README.md"
    "LICENSE"
    "CITATION.cff"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    "CHANGELOG.md"
    "SUPPORT.md"
    "THIRD_PARTY_NOTICES.md"
    "pyproject.toml"
    ".gitignore"
    ".gitattributes"
    ".editorconfig"
    ".pre-commit-config.yaml"
    "src/icebrew/__init__.py"
    "src/icebrew/__main__.py"
    "src/icebrew/cli/__init__.py"
    "src/icebrew/core/__init__.py"
    "src/icebrew/core/exceptions.py"
    "src/icebrew/core/logging.py"
    "src/icebrew/configuration/__init__.py"
    "src/icebrew/diagnostics/__init__.py"
    "src/icebrew/diagnostics/result.py"
    "src/icebrew/diagnostics/engine.py"
    "tests/conftest.py"
    "tests/unit/test_core.py"
    "config/defaults.yaml"
)

echo "[Icebrew] Creating repository directories..."

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
done

echo "[Icebrew] Creating foundational files..."

for file in "${files[@]}"; do
    if [[ ! -e "$file" ]]; then
        touch "$file"
    fi
done

echo
echo "[Icebrew] Scaffold completed successfully."
echo "[Icebrew] Project root: $ROOT_DIR"
