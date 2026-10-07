#!/usr/bin/env bash
# Public exercise checker; Python's stdlib runner asserts real HTTP contracts.
set -eu
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [[ ! "$1" =~ ^[1-79]$ ]]; }; then
  echo "Usage: ./verify.sh [1-7|9] (8 and 10 are manual activities)" >&2
  exit 2
fi
case "${1:-all}" in
  1) tests=(BackendDeclarationTests) ;;
  2) tests=(RoutingTests) ;;
  3) tests=(CacheTests) ;;
  4) tests=(TTLVaryTests) ;;
  5) tests=(GraceTests) ;;
  6) tests=(PurgeTests) ;;
  7) tests=(DirectorTests) ;;
  9) tests=(TroubleshootingTests) ;;
  all) tests=(BackendTests RoutingTests CacheTests TTLVaryTests PurgeTests DirectorTests TroubleshootingTests GraceTests) ;;
esac
root="$(dirname "$0")"
exec "${PYTHON:-python3}" "$root/tests/lab_tests.py" "${tests[@]}"
