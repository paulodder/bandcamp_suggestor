#!/bin/sh

echo "-- INITIALIZING --"

echo "** Checking network connection"
# Wait for network connection
x=0
while [ ifconfig | grep "192.168.100." > /dev/null ]; do
    echo "** Waiting for network (${x})"
    if "$x" -gt 200; then
        # Time out here
        echo "** Connection to network not established, exiting"
        exit 1
    x=$((x+1))
    sleep .1
    fi
done
echo "** Connected to network"

# Pull any new changes
echo "** Pulling latest changes from bandcamp_suggestor"
git -C /home/lucw/Documents/bandcamp_suggestor/ pull origin main

# Run the script
echo "** Running bandcamp_suggestor"
/home/lucw/Documents/bandcamp_suggestor/bandcamp/bin/python3 /home/lucw/Documents/bandcamp_suggestor/scripts/play_recommendation.py
