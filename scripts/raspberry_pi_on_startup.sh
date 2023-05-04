#!/bin/sh

echo "-- INITIALIZING --"

# Pull any new changes
echo "** Pulling latest changes from bandcamp_suggestor"
git config --global --add safe.directory /home/lucw/Documents/bandcamp_suggestor
git -C /home/lucw/Documents/bandcamp_suggestor/ pull origin main

# Run the script
echo "** Running bandcamp_suggestor"
sudo /home/lucw/Documents/bandcamp_suggestor/bandcamp/bin/python3 /home/lucw/Documents/bandcamp_suggestor/scripts/play_recommendation.py &
