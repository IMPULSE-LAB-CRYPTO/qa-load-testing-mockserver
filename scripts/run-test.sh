#!/usr/bin/env bash
#
# Runs a full headless load test against MockServer.
#
# Usage:
#   bash scripts/run-test.sh [duration] [users] [spawn-rate]
#
# Defaults:
#   duration   = 1h
#   users      = 200
#   spawn-rate = 20

set -euo pipefail

DURATION="${1:-1h}"
USERS="${2:-200}"
SPAWN_RATE="${3:-20}"

REPORT_DIR="locust/reports"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
PREFIX="${REPORT_DIR}/full-test-${TIMESTAMP}"

mkdir -p "${REPORT_DIR}"

echo "==> Starting load test"
echo "    duration   : ${DURATION}"
echo "    users      : ${USERS}"
echo "    spawn-rate : ${SPAWN_RATE}"
echo "    reports    : ${PREFIX}.*"
echo

docker compose exec -T locust locust \
  -f /mnt/locust/locustfile.py \
  --host http://mockserver:1080 \
  --headless \
  -u "${USERS}" \
  -r "${SPAWN_RATE}" \
  --run-time "${DURATION}" \
  --csv "/mnt/locust/reports/full-test-${TIMESTAMP}" \
  --html "/mnt/locust/reports/full-test-${TIMESTAMP}.html" \
  --only-summary

echo
echo "==> Test finished. Reports saved to ${REPORT_DIR}/"