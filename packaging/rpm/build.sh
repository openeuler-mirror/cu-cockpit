#!/usr/bin/env bash
set -euo pipefail

# Build RPM for OSManager. Run on a RHEL/CentOS/Rocky machine with rpmbuild installed.

PKG_NAME=osmanager
VERSION=1.0.0
WORKDIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$WORKDIR/../.." && pwd)

RPMBUILD=${RPMBUILD:-$HOME/rpmbuild}
SOURCES="$RPMBUILD/SOURCES"
SPECS="$RPMBUILD/SPECS"

mkdir -p "$SOURCES" "$SPECS"

# Prepare source tarball (project root to be extracted under osmanager-src/)
TMP_SRC=$(mktemp -d)
trap 'rm -rf "$TMP_SRC"' EXIT

mkdir -p "$TMP_SRC/osmanager-src"

# Copy project (exclude node_modules/tests/.git artifacts)
rsync -a --delete \
  --exclude ".git" \
  --exclude "web/node_modules" \
  --exclude "**/__pycache__" \
  --exclude "**/*.pyc" \
  "$ROOT/" "$TMP_SRC/osmanager-src/"

# Place a LICENSE if exists at top-level
if [[ -f "$ROOT/LICENSE" ]]; then
  cp "$ROOT/LICENSE" "$TMP_SRC/osmanager-src/"
fi

tar -C "$TMP_SRC" -czf "$SOURCES/${PKG_NAME}-src.tar.gz" osmanager-src

# Copy spec and extra sources, and convert CRLF to LF (fix Windows line endings)
cp "$WORKDIR/${PKG_NAME}.spec" "$SPECS/"
# Remove Windows line endings (CRLF -> LF) from spec file
sed -i 's/\r$//' "$SPECS/${PKG_NAME}.spec"

cp "$WORKDIR/osmanager.service" "$SOURCES/"
sed -i 's/\r$//' "$SOURCES/osmanager.service"

cp "$WORKDIR/custom-webssh.service" "$SOURCES/"
sed -i 's/\r$//' "$SOURCES/custom-webssh.service"

cp "$WORKDIR/requirements.txt" "$SOURCES/"
sed -i 's/\r$//' "$SOURCES/requirements.txt"

cp "$WORKDIR/start_webssh.sh" "$SOURCES/"
sed -i 's/\r$//' "$SOURCES/start_webssh.sh"
chmod +x "$SOURCES/start_webssh.sh"

# Use osmanager/os.env if exists (with ip placeholders), fallback to root os.env
if [[ -f "$ROOT/osmanager/os.env" ]]; then
  cp "$ROOT/osmanager/os.env" "$SOURCES/os.env"
  sed -i 's/\r$//' "$SOURCES/os.env"
  echo "Using osmanager/os.env (with ip placeholders)"
elif [[ -f "$ROOT/os.env" ]]; then
  cp "$ROOT/os.env" "$SOURCES/os.env"
  sed -i 's/\r$//' "$SOURCES/os.env"
  echo "Using root os.env"
else
  cat > "$SOURCES/os.env" <<'EOF'
DJANGO_SETTINGS_MODULE=osmanager.settings
DEBUG=False
ALLOWED_HOSTS=ip,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://ip:8080
BACKEND_BIND=ip:8000
HOST_IP=ip
EOF
  echo "Created default os.env with ip placeholders"
fi

rpmbuild -ba "$SPECS/${PKG_NAME}.spec"

echo "\nBuild complete. Find RPMs under $RPMBUILD/RPMS/"

