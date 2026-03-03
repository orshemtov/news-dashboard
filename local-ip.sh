#!/bin/bash

# Detect local IP address on macOS (en0 is typical WiFi)
LOCAL_IP=$(ipconfig getifaddr en0)

if [ -z "$LOCAL_IP" ]; then
    # Fallback for Linux if needed (e.g. if running in WSL or similar)
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

echo "------------------------------------------------"
echo "Local Dashboard Access"
echo "------------------------------------------------"
if [ -n "$LOCAL_IP" ]; then
    echo "1. http://news.local  (Should work on iPhone/iPad/Mac)"
    echo "2. http://news.home   (Requires Router DNS mapping to $LOCAL_IP)"
    echo "3. http://$LOCAL_IP     (Direct IP access)"
else
    echo "Could not detect local IP, but http://news.local should still work."
fi
echo "------------------------------------------------"
