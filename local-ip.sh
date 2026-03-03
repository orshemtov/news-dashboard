#!/bin/bash

# Detect local IP address on macOS (en0 is typical WiFi)
LOCAL_IP=$(ipconfig getifaddr en0)

if [ -z "$LOCAL_IP" ]; then
    # Fallback for Linux if needed (e.g. if running in WSL or similar)
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

if [ -n "$LOCAL_IP" ]; then
    # Create or update .env.local with the current IP
    if grep -q "LOCAL_IP=" .env.docker 2>/dev/null; then
        sed -i '' "s/LOCAL_IP=.*/LOCAL_IP=$LOCAL_IP/" .env.docker
    else
        echo "LOCAL_IP=$LOCAL_IP" >> .env.docker
    fi
    echo "LOCAL_IP set to $LOCAL_IP in .env.docker"
else
    echo "Could not detect local IP."
    exit 1
fi
