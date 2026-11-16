#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SYSTEMD_UNIT_DIR=${SYSTEMD_UNIT_DIR:-/etc/systemd/system}
APP_DIR=${APP_DIR:-/opt/cu-cockpit}

if [[ ! $APP_DIR =~ ^/[A-Za-z0-9._/-]+$ || $APP_DIR == *//* ||
      $APP_DIR == */../* || $APP_DIR == */./* || $APP_DIR == */.. ||
      $APP_DIR == */. || $APP_DIR == */ ]]; then
    echo "APP_DIR must be a safe absolute path" >&2
    exit 2
fi

install -d -m 0755 "$SYSTEMD_UNIT_DIR"
sed "s|/opt/cu-cockpit|$APP_DIR|g" "$SCRIPT_DIR/cu-cockpit-backup.service" \
    > "$SYSTEMD_UNIT_DIR/cu-cockpit-backup.service"
chmod 0644 "$SYSTEMD_UNIT_DIR/cu-cockpit-backup.service"
install -m 0644 "$SCRIPT_DIR/cu-cockpit-backup.timer" "$SYSTEMD_UNIT_DIR/cu-cockpit-backup.timer"

if [[ ${SKIP_SYSTEMCTL:-false} == true ]]; then
    exit 0
fi

systemd-analyze verify "$SYSTEMD_UNIT_DIR/cu-cockpit-backup.service" \
    "$SYSTEMD_UNIT_DIR/cu-cockpit-backup.timer"
systemctl daemon-reload
systemctl enable --now cu-cockpit-backup.timer
