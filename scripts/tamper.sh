#!/usr/bin/env bash
set -euo pipefail
FILE="$1"
# simulate tampering
printf '\n' >> "$FILE"
echo "Tampered $FILE"
# leave the original checksum untouched so mismatches are detected
