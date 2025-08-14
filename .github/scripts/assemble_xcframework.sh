#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --device-lib <path.a> --sim-libs <path1.a,path2.a> --name <Name> --out <dir>"
  exit 1
}

DEVICE=""
SIMS=""
NAME=""
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device-lib) DEVICE="$2"; shift 2 ;;
    --sim-libs)   SIMS="$2"; shift 2 ;;
    --name)       NAME="$2"; shift 2 ;;
    --out)        OUT="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$DEVICE" && -n "$SIMS" && -n "$NAME" && -n "$OUT" ]] || usage

mkdir -p "$OUT"
IFS=',' read -r -a SIM_ARRAY <<< "$SIMS"

XC_ARGS=( -create-xcframework -library "$DEVICE" )
for s in "${SIM_ARRAY[@]}"; do
  XC_ARGS+=( -library "$s" )
done
XC_ARGS+=( -output "$OUT/$NAME.xcframework" )

xcodebuild "${XC_ARGS[@]}"
echo "Wrote $OUT/$NAME.xcframework"
