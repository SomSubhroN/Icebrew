#!/usr/bin/env bash

set -euo pipefail

# ==========================================================
# Icebrew Linux Installer
# ==========================================================

echo
echo "=========================================="
echo "          ICEBREW INSTALLER"
echo "          Brew your experiments."
echo "=========================================="
echo

# ----------------------------------------------------------
# 1. Locate project root
# ----------------------------------------------------------

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "[INFO] Project root: $PROJECT_ROOT"

# ----------------------------------------------------------
# 2. Check Git
# ----------------------------------------------------------

if ! command -v git >/dev/null 2>&1; then
    echo "[ERROR] Git is not installed."
    echo "Install Git using your distribution's package manager."
    exit 1
fi

echo "[OK] Git detected."

# ----------------------------------------------------------
# 3. Detect Python
# ----------------------------------------------------------

if command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
else
    echo "[ERROR] Python 3 was not found."
    exit 1
fi

echo "[INFO] Python executable: $PYTHON"

# ----------------------------------------------------------
# 4. Validate Python version
# ----------------------------------------------------------

PYTHON_VERSION="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

IFS='.' read -r PYTHON_MAJOR PYTHON_MINOR <<< "$PYTHON_VERSION"

if [[ "$PYTHON_MAJOR" -ne 3 || "$PYTHON_MINOR" -lt 12 || "$PYTHON_MINOR" -ge 15 ]]; then
    echo "[ERROR] Icebrew requires Python 3.12, 3.13 or 3.14."
    echo "[ERROR] Detected Python $PYTHON_VERSION."
    exit 1
fi

echo "[OK] Python $PYTHON_VERSION detected."

# ----------------------------------------------------------
# 5. Define installation paths
# ----------------------------------------------------------

INSTALL_DIR="$HOME/.local/share/icebrew"
VENV_DIR="$INSTALL_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_EXECUTABLE="$VENV_DIR/bin/icebrew"

USER_BIN="$HOME/.local/bin"
LAUNCHER="$USER_BIN/icebrew"

# ----------------------------------------------------------
# 6. Create installation directories
# ----------------------------------------------------------

mkdir -p "$INSTALL_DIR"
mkdir -p "$USER_BIN"

echo "[INFO] Installation directory: $INSTALL_DIR"

# ----------------------------------------------------------
# 7. Create virtual environment
# ----------------------------------------------------------

if [[ ! -x "$VENV_PYTHON" ]]; then

    echo "[INFO] Creating virtual environment..."

    "$PYTHON" -m venv "$VENV_DIR"

else

    echo "[INFO] Existing virtual environment detected."

fi

# ----------------------------------------------------------
# 8. Install Icebrew
# ----------------------------------------------------------

echo "[INFO] Installing Icebrew..."

"$VENV_PYTHON" -m pip install --upgrade pip

"$VENV_PYTHON" -m pip install "$PROJECT_ROOT"

# ----------------------------------------------------------
# 9. Create user launcher
# ----------------------------------------------------------

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
exec "$VENV_EXECUTABLE" "\$@"
EOF

chmod +x "$LAUNCHER"

echo "[OK] Launcher created."

# ----------------------------------------------------------
# 10. Configure PATH in ~/.profile
# ----------------------------------------------------------

PROFILE="$HOME/.profile"
PATH_MARKER="# Icebrew PATH configuration"

if [[ ! -f "$PROFILE" ]]; then
    touch "$PROFILE"
fi

if ! grep -Fq "$PATH_MARKER" "$PROFILE"; then

    cat >> "$PROFILE" <<EOF

$PATH_MARKER
export PATH="\$HOME/.local/bin:\$PATH"
EOF

    echo "[INFO] PATH configuration added to ~/.profile."

else

    echo "[INFO] PATH configuration already exists."

fi

# ----------------------------------------------------------
# 11. Verify installation
# ----------------------------------------------------------

if [[ ! -x "$LAUNCHER" ]]; then
    echo "[ERROR] Installation verification failed."
    exit 1
fi

"$LAUNCHER" version

# ----------------------------------------------------------
# 12. Completion
# ----------------------------------------------------------

echo
echo "=========================================="
echo "       ICEBREW INSTALLED SUCCESSFULLY"
echo "=========================================="
echo
echo "Installation directory: $INSTALL_DIR"
echo "Launcher: $LAUNCHER"
echo
echo "Restart your shell or run:"
echo "    source ~/.profile"
echo
echo "Then run:"
echo "    icebrew --help"
echo