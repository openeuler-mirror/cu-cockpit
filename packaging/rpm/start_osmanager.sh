#!/bin/bash
# OSManager startup script with delayed dependency installation

OSM_DIR="/opt/chinaunicom/osmanager"
APP_VENV="$OSM_DIR/venv"
OSM_ENV="$OSM_DIR/os.env"
SETUP_MARKER="$APP_VENV/.setup_complete"

# Function to check custom PyPI mirror access
check_pypi_mirror() {
    if grep -q "pypi.culinux.net" /etc/hosts 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to install with fallback to custom mirror
install_with_fallback() {
    local cmd="$1"
    local name="$2"
    
    # First check if we have internet connectivity
    if timeout 5 ping -c 1 pypi.org >/dev/null 2>&1; then
        # We have internet, use default PyPI directly
        echo "Installing $name using default PyPI repository..."
        if $cmd; then
            return 0
        fi
    else
        echo "No internet connectivity detected"
    fi
    
    # If failed, try custom mirror if available
    if check_pypi_mirror; then
        echo "Trying custom PyPI mirror for $name..."
        $cmd --index-url https://pypi.culinux.net/simple
        return $?
    else
        echo "INFO: 172.25.14.15  pypi.culinux.net not configured in /etc/hosts" >&2   
    fi
    
    return 1
}

# Function to get host IP address
get_host_ip() {
    # Try multiple methods to get host IP
    local HOST_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk 'NR==1 {print $7}')
    if [ -z "$HOST_IP" ] || [ "$HOST_IP" = "" ]; then
        # fallback to ip route
        HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    if [ -z "$HOST_IP" ] || [ "$HOST_IP" = "" ]; then
        # fallback to hostname -i
        HOST_IP=$(hostname -i 2>/dev/null | awk '{print $1}')
    fi
    if [ -z "$HOST_IP" ] || [ "$HOST_IP" = "" ]; then
        # last resort: use localhost
        HOST_IP="127.0.0.1"
        echo "WARNING: Could not detect host IP, using 127.0.0.1" >&2
    fi
    echo "$HOST_IP"
}

# Function to replace 'ip' placeholders in os.env file
replace_ip_placeholders() {
    local OSM_DIR="/opt/chinaunicom/osmanager"
    local OSM_ENV="$OSM_DIR/os.env"
    
    # Get host IP
    local HOST_IP=$(get_host_ip)
    
    if [ -f "$OSM_ENV" ]; then
        # Use a temporary file for safety
        if cp "$OSM_ENV" "$OSM_ENV.tmp" 2>/dev/null; then
            # Replace literal 'ip' tokens (not substrings in words) in os.env
            # Use word boundary to match only 'ip' as a separate word
            sed -E "s/\bip\b/$HOST_IP/g" "$OSM_ENV.tmp" > "$OSM_ENV.new" && \
            mv "$OSM_ENV.new" "$OSM_ENV" && \
            rm -f "$OSM_ENV.tmp" "$OSM_ENV.new" && \
            echo "INFO: Replaced 'ip' with '$HOST_IP' in $OSM_ENV" || \
            echo "WARNING: Failed to update $OSM_ENV" >&2
        else
            echo "WARNING: No write permission to update $OSM_ENV" >&2
        fi
    fi
    
    # Update nginx configuration
    local CONF="/etc/nginx/conf.d/cu-cockpit-web.conf"
    if [ -f "$CONF" ]; then
        echo "Updating nginx configuration with IP: $HOST_IP"
        sed -i "s|proxy_pass  http://127\.0\.0\.1:8000;|proxy_pass  http://${HOST_IP}:8000;|" "$CONF"
        # Test and reload nginx
        if nginx -t; then
            systemctl reload nginx && echo "Nginx reload success" || echo "Nginx reload failed"
        else
            echo "Nginx configuration test failed"
        fi
    else
        echo "Nginx configuration file not found: $CONF"
    fi
}
# Replace IP placeholders before starting the server
replace_ip_placeholders
# Check if initial setup is needed (skip if marker file exists)
if [ ! -f "$SETUP_MARKER" ]; then
    # Create virtual environment if it doesn't exist
    if [ ! -d "$APP_VENV" ]; then
        echo "Creating virtual environment..."
        python3 -m venv --system-site-packages "$APP_VENV" || {
            echo "ERROR: Failed to create virtual environment" >&2
            exit 1
        }
    fi

    # Update pip with fallback
    echo "Updating pip..."
    #install_with_fallback "\"$APP_VENV/bin/pip\" install --upgrade pip" "pip" || true
    install_with_fallback "$APP_VENV/bin/pip install --upgrade pip" "pip" || true

    # Install Python packages from requirements.txt if it exists
    if [ -f "$OSM_DIR/requirements.txt" ]; then
        echo "Installing Python dependencies..."
        install_with_fallback "$APP_VENV/bin/pip install -r $OSM_DIR/requirements.txt" "dependencies" || {
        #install_with_fallback "\"$APP_VENV/bin/pip\" install -r \"$OSM_DIR/requirements.txt\"" "dependencies" || {
            echo "WARNING: Some packages failed to install" >&2
        }
    fi
    
    # Run Django database migrations
    if [ -f "$OSM_DIR/manage.py" ]; then
        echo "Running Django database migrations..."
        cd "$OSM_DIR"
        
        # Source the environment file to get Django settings
        if [ -f "$OSM_ENV" ]; then
            set -a
            source "$OSM_ENV"
            set +a
        fi
        
        # Run migrations (non-interactive, fake-initial if needed)
        "$APP_VENV/bin/python" manage.py migrate --noinput || {
            echo "WARNING: Database migrations failed. You may need to run them manually." >&2
            echo "Run: cd $OSM_DIR && source $OSM_ENV && $APP_VENV/bin/python manage.py migrate" >&2
        }
    fi
    
    # Create marker file to indicate setup is complete
    touch "$SETUP_MARKER"
    echo "Initial setup (dependencies installation and database migrations) completed."
else
    echo "Initial setup already completed, skipping."
fi

# Start the Django development server
echo "Starting Django development server..."

"$APP_VENV/bin/python" "$OSM_DIR/manage.py" runserver "$BACKEND_BIND"
