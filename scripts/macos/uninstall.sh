#!/usr/bin/env bash

set -euo pipefail

# ==========================================================
# Icebrew macOS Uninstaller
# ==========================================================

echo
echo "=========================================="
echo "          ICEBREW UNINSTALLER"
echo "=========================================="
echo

# ----------------------------------------------------------
# 1. Verify operating system
# ----------------------------------------------------------

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "[ERROR] This uninstaller is intended for macOS."
    exit 1
fi

# ----------------------------------------------------------
# 2. Define installation paths
# ----------------------------------------------------------

INSTALL_DIR="$HOME/.local/share/icebrew"
USER_BIN="$HOME/.local/bin"
LAUNCHER="$USER_BIN/icebrew"
PROFILE="$HOME/.zprofile"
PATH_MARKER="# Icebrew PATH configuration"

# ----------------------------------------------------------
# 3. Check installation
# ----------------------------------------------------------

if [[ ! -d "$INSTALL_DIR" && ! -f "$LAUNCHER" ]]; then

    echo "[INFO] Icebrew installation was not found."
    exit 0

fi

echo "[INFO] Icebrew installation detected."

# ----------------------------------------------------------
# 4. Remove managed installation
# ----------------------------------------------------------

if [[ -d "$INSTALL_DIR" ]]; then

    echo "[INFO] Removing managed installation..."

    rm -rf -- "$INSTALL_DIR"

fi

# ----------------------------------------------------------
# 5. Remove launcher
# ----------------------------------------------------------

if [[ -f "$LAUNCHER" ]]; then

    rm -f -- "$LAUNCHER"

    echo "[OK] Launcher removed."

fi

# ----------------------------------------------------------
# 6. Remove PATH configuration
# ----------------------------------------------------------

if [[ -f "$PROFILE" ]] && grep -Fq "$PATH_MARKER" "$PROFILE"; then

    TEMP_PROFILE="$(mktemp)"

    awk '
        $0 == "# Icebrew PATH configuration" {
            skip = 1
            next
        }

        skip && /^export PATH="\$HOME\/\.local\/bin:\$PATH"$/ {
            skip = 0
            next
        }

        skip {
            skip = 0
        }

        { print }
    ' "$PROFILE" > "$TEMP_PROFILE"

    cat "$TEMP_PROFILE" > "$PROFILE"

    rm -f "$TEMP_PROFILE"

    echo "[OK] Icebrew PATH configuration removed."

fi

# ----------------------------------------------------------
# 7. Verify removal
# ----------------------------------------------------------

if [[ -d "$INSTALL_DIR" || -f "$LAUNCHER" ]]; then

    echo "[ERROR] Uninstallation verification failed."
    exit 1

fi

# ----------------------------------------------------------
# 8. Completion
# ----------------------------------------------------------

echo
echo "=========================================="
echo "       ICEBREW UNINSTALLED"
echo "=========================================="
echo
echo "Icebrew has been removed."
echo "Your datasets and unrelated files were not touched."
echo
