#!/usr/bin/env bash
# FP-006 AC-15 (Flutter port): fail if any known fabricated agricultural output
# appears in lib/. Same blocklist as frontend/scripts/check-no-fabrication.mjs.
# Exit 1 on any hit, printing file:line.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$ROOT/lib"

BLOCKLIST=(
  "Magnaporthe"
  "Tricyclazole"
  "K. Raja"
  "ராஜா"
  "ADT 43"
  "2320"
  "முருகன்"
  "Eligible"
  "postpone urea"
  "Sell Recommendation"
  "விற்பனை பரிந்துரை"
  "அடிப்படையில்"
  "இயக்கப்படுகிறது"
  "4.2 km"
)

hits=0
for term in "${BLOCKLIST[@]}"; do
  # -F fixed string, -r recursive, -n line numbers; include Dart + ARB + JSON.
  if out=$(grep -rnF --include='*.dart' --include='*.arb' --include='*.json' -- "$term" "$TARGET"); then
    while IFS= read -r line; do
      echo "  ${line#"$ROOT/"}: \"$term\"" >&2
      hits=$((hits + 1))
    done <<< "$out"
  fi
done

if [ "$hits" -gt 0 ]; then
  echo "check_no_fabrication: $hits blocked string(s) found in lib/" >&2
  exit 1
fi
echo "check_no_fabrication: OK (${#BLOCKLIST[@]} blocked strings, 0 hits in lib/)"
