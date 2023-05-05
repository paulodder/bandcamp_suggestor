#!/bin/sh

echo "-- INITIALIZING --"

# Pull any new changes
echo "** Pulling latest changes from bandcamp_suggestor"
say "Updating"
sudo /home/lucw/Documents/bandcamp_suggestor/bandcamp/bin/python3 /home/lucw/Documents/bandcamp_suggestor/scripts/pull_git.py

# Run the script
echo "** Running bandcamp_suggestor"
say "Starting radio"
sudo /home/lucw/Documents/bandcamp_suggestor/bandcamp/bin/python3 /home/lucw/Documents/bandcamp_suggestor/scripts/play_recommendation.py &
