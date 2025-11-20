#!/usr/bin/env bash
# SmartLogWatcher - Main Monitoring Daemon

CONFIG="/etc/smartlogwatcher.conf"
source "$CONFIG"

LOGFILE="${LOG_FILE:-/var/log/auth.log}"

mkdir -p "$DATA_DIR" "$RUNTIME_DIR" "$REPORT_DIR"
touch "$SUSPICIOUS_LOG" "$BLOCKED_FILE"

echo $$ > "${RUNTIME_DIR}/smartlogwatcher.pid"

record_failure() {
  ip=$1
  tsdir="$DATA_DIR/ip_attempts"
  mkdir -p "$tsdir"
  tsfile="$tsdir/$ip.timestamps"
  now=$(date +%s)
  echo "$now" >> "$tsfile"
  awk -v n=$now -v w=$WINDOW_SECONDS '{ if (n-$1 <= w) print }' "$tsfile" > "$tsfile.tmp"
  mv "$tsfile.tmp" "$tsfile"
  wc -l < "$tsfile"
}

block_ip() {
  ip=$1
  reason=$2
  /usr/local/bin/smartlogwatcher_block.sh block "$ip" "$BLOCK_DURATION_SECONDS" "$reason"
}

echo "SmartLogWatcher Started..."

tail -n0 -F "$LOGFILE" | while read -r line; do
  if echo "$line" | grep -E "$FAIL_PATTERNS" >/dev/null; then
    ip=$(echo "$line" | sed -nE 's/.*from ([^ ]+).*/\1/p')
    user=$(echo "$line" | sed -nE 's/.*for (invalid user )?([^ ]+).*/\2/p')
    echo "$(date --iso-8601=seconds) DETECT: $ip user=$user" >> "$SUSPICIOUS_LOG"
    count=$(record_failure "$ip")
    if (( count >= THRESHOLD )); then
      block_ip "$ip" "exceeded threshold"
    fi
  fi
done
