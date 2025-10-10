#!/usr/bin/env bash
set -euo pipefail
FILE="$1"
# simulate tampering
echo "" >> "$FILE"
echo "Tampered $FILE"
# the checksum after tampering
shasum -a 256 "$FILE" | awk '{print $1}' > "${FILE}.sha256"
echo "New checksum written to ${FILE}.sha256"