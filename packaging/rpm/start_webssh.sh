#!/bin/bash
# WebSSH startup script with IP detection

OSM_ENV="/opt/chinaunicom/osmanager/os.env"

# Try to get IP from os.env HOST_IP variable first (added by RPM install script)
if [ -f "$OSM_ENV" ]; then
    IP=$(grep "^HOST_IP=" "$OSM_ENV" 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" | xargs)
fi

# If not found in HOST_IP, try to extract from CSRF_TRUSTED_ORIGINS
if [ -z "$IP" ] && [ -f "$OSM_ENV" ]; then
    IP=$(grep "^CSRF_TRUSTED_ORIGINS=http://" "$OSM_ENV" 2>/dev/null | sed -E 's|^CSRF_TRUSTED_ORIGINS=http://([^:]+).*|\1|' | xargs)
fi

# If still not found, try multiple system methods
if [ -z "$IP" ]; then
    IP=$(hostname -I 2>/dev/null | awk '{print $1}' | xargs)
fi

if [ -z "$IP" ]; then
    IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk 'NR==1 {print $7}' | xargs)
fi

if [ -z "$IP" ]; then
    IP=$(hostname -i 2>/dev/null | awk '{print $1}' | xargs)
fi

# Last resort
if [ -z "$IP" ]; then
    IP="127.0.0.1"
fi

exec /opt/chinaunicom/osmanager/venv/bin/wssh \
    --address=127.0.0.1 \
    --port=8001 \
    --origin="http://${IP}:8080" \
    --xsrf=True \
    --delay=30

