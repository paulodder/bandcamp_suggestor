#!/bin/sh

echo "-- INITIALIZING --"

# Pull any new changes
echo "** Pulling latest changes from bandcamp_suggestor"
say "Pulling in changes"
sudo /home/lucw/Documents/bandcamp_suggestor/bandcamp/bin/python3 /home/lucw/Documents/bandcamp_suggestor/scripts/pull_git.py

# Run the script
echo "** Running bandcamp_suggestor"
say "Running bandcamp suggestor"
sudo /home/lucw/Documents/bandcamp_suggestor/bandcamp/bin/python3 /home/lucw/Documents/bandcamp_suggestor/scripts/play_recommendation.py &
