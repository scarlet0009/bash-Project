#!/usr/bin/env bash
CONFIG="/etc/smartlogwatcher.conf"
source "$CONFIG"

logf() { echo "$(date --iso-8601=seconds) $1" >> "$SUSPICIOUS_LOG"; }

case "$1" in
  block)
    ip=$2
    dur=$3
    reason=$4
    now=$(date +%s)
    end=$((now+dur))
    echo "$ip,$now,$end,$reason" >> "$BLOCKED_FILE"
    iptables -C INPUT -s "$ip" -j DROP 2>/dev/null || iptables -I INPUT -s "$ip" -j DROP
    logf "BLOCKED: $ip reason=$reason"
    ;;
  unblock)
    ip=$2
    iptables -D INPUT -s "$ip" -j DROP 2>/dev/null
    grep -v "^$ip," "$BLOCKED_FILE" > "$BLOCKED_FILE.tmp" && mv "$BLOCKED_FILE.tmp" "$BLOCKED_FILE"
    logf "UNBLOCKED: $ip"
    ;;
esac
