#!/bin/bash

# Detect local IP address on macOS (en0 is typical WiFi)
LOCAL_IP=$(ipconfig getifaddr en0)

if [ -z "$LOCAL_IP" ]; then
    # Fallback for Linux if needed (e.g. if running in WSL or similar)
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

if [ -n "$LOCAL_IP" ]; then
    # Ensure .env exists
    touch .env
    
    # Update LOCAL_IP in .env (standard for Docker Compose)
    if grep -q "LOCAL_IP=" .env; then
        # Use a temporary file for sed to avoid some macOS vs Linux differences
        sed "s/LOCAL_IP=.*/LOCAL_IP=$LOCAL_IP/" .env > .env.tmp && mv .env.tmp .env
    else
        echo "LOCAL_IP=$LOCAL_IP" >> .env
    fi
    echo "LOCAL_IP set to $LOCAL_IP in .env"
else
    echo "Could not detect local IP."
    exit 1
fi
