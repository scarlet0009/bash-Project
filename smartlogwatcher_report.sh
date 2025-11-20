#!/usr/bin/env bash
CONFIG="/etc/smartlogwatcher.conf"
source "$CONFIG"

REPORT_FILE="$REPORT_DIR/report-$(date +%F).txt"

{
  echo "SmartLogWatcher Report - $(date)"
  echo
  echo "Blocked IPs:"
  cat "$BLOCKED_FILE"
  echo
  echo "Recent Suspicious Activity:"
  tail -n 50 "$SUSPICIOUS_LOG"
} > "$REPORT_FILE"

echo "Report saved: $REPORT_FILE"
