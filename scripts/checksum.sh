#!/usr/bin/env bash
set -euo pipefail
FILE="$1"
shasum -a 256 "$FILE" | awk '{print $1}' > "${FILE}.sha256"
echo "Checksum written to ${FILE}.sha256"
cat "${FILE}.sha256"
