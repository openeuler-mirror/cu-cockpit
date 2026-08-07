#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SYSTEMD_UNIT_DIR=${SYSTEMD_UNIT_DIR:-/etc/systemd/system}

install -d -m 0755 "$SYSTEMD_UNIT_DIR"
install -m 0644 "$SCRIPT_DIR/cu-cockpit-metrics.service" "$SYSTEMD_UNIT_DIR/cu-cockpit-metrics.service"
install -m 0644 "$SCRIPT_DIR/cu-cockpit-metrics.timer" "$SYSTEMD_UNIT_DIR/cu-cockpit-metrics.timer"

if [[ ${SKIP_SYSTEMCTL:-false} == true ]]; then
    exit 0
fi

systemctl daemon-reload
systemctl enable --now cu-cockpit-metrics.timer