# scripts/run-test.ps1
param(
    [string]$Duration = "1h"
)

$ErrorActionPreference = "Stop"

$ReportDir = "locust/reports"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Prefix    = "$ReportDir/full-test-$Timestamp"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

Write-Host "==> Starting load test"
Write-Host "    duration : $Duration"
Write-Host "    profile  : init=30 rps, second=20 rps, third=10 rps"
Write-Host "    users    : 60 (30 + 20 + 10)"
Write-Host "    reports  : $Prefix.*"
Write-Host ""

docker compose exec -T locust locust `
  -f /mnt/locust/locustfile.py `
  --host http://mockserver:1080 `
  --headless `
  -u 60 `
  -r 6 `
  --run-time $Duration `
  --csv "/mnt/locust/reports/full-test-$Timestamp" `
  --html "/mnt/locust/reports/full-test-$Timestamp.html" `
  --only-summary

Write-Host ""
Write-Host "==> Test finished. Reports saved to $ReportDir/"