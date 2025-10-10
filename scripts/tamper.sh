#!/usr/bin/env bash
set -euo pipefail
FILE="$1"
# simulate tampering
printf '\n' >> "$FILE"
echo "Tampered $FILE"
