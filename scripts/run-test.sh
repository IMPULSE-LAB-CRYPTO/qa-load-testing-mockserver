#!/usr/bin/env bash
#
# Runs a full headless load test against MockServer with the target
# 30/20/10 RPS profile.
#
# Usage:
#   bash scripts/run-test.sh [duration]
#
# Defaults:
#   duration = 1h

set -euo pipefail

DURATION="${1:-1h}"
REPORT_DIR="locust/reports"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
PREFIX="${REPORT_DIR}/full-test-${TIMESTAMP}"

mkdir -p "${REPORT_DIR}"

echo "==> Starting load test"
echo "    duration : ${DURATION}"
echo "    profile  : init=30 rps, second=20 rps, third=10 rps"
echo "    users    : 60 (30 + 20 + 10)"
echo "    reports  : ${PREFIX}.*"
echo

docker compose exec -T locust locust \
  -f /mnt/locust/locustfile.py \
  --host http://mockserver:1080 \
  --headless \
  -u 60 \
  -r 6 \
  --run-time "${DURATION}" \
  --csv "/mnt/locust/reports/full-test-${TIMESTAMP}" \
  --html "/mnt/locust/reports/full-test-${TIMESTAMP}.html" \
  --only-summary

echo
echo "==> Test finished. Reports saved to ${REPORT_DIR}/"