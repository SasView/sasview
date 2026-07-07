#!/usr/bin/env bash
# Build a drag-to-Applications DMG for SasView on macOS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/installers/dist"
STAGING_DIR="${DIST_DIR}/dmg-staging"
APP_NAME="SasView6.app"
DMG_NAME="${1:-SasView6.dmg}"
BACKGROUND="${SCRIPT_DIR}/dmg_background.png"
VOLUME_NAME="Install SasView"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "create_dmg.sh must be run on macOS." >&2
    exit 1
fi

if [[ ! -d "${DIST_DIR}/${APP_NAME}" ]]; then
    echo "Expected ${DIST_DIR}/${APP_NAME} to exist. Build the app bundle first." >&2
    exit 1
fi

if [[ ! -f "${BACKGROUND}" ]]; then
    echo "Missing ${BACKGROUND}." >&2
    exit 1
fi

if ! command -v dmgbuild >/dev/null 2>&1; then
    echo "dmgbuild is required. Install with: pip install dmgbuild" >&2
    exit 1
fi

rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"
cp -R "${DIST_DIR}/${APP_NAME}" "${STAGING_DIR}/"

rm -f "${DIST_DIR}/${DMG_NAME}"

dmgbuild -s "${SCRIPT_DIR}/dmg_settings.py" \
    -D "staging_dir=${STAGING_DIR}" \
    -D "app_name=${APP_NAME}" \
    -D "background=${BACKGROUND}" \
    "${VOLUME_NAME}" \
    "${DIST_DIR}/${DMG_NAME}"

echo "Created ${DIST_DIR}/${DMG_NAME}"
