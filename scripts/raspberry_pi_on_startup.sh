#!/bin/sh

# Usage:
# Give this file execute permissions
# chmod +x path/to/raspberry_pi_on_startup.sh
# Then do the following on startup of raspberry pi (https://unix.stackexchange.com/questions/166473/debian-how-to-run-a-script-on-startup-as-soon-as-there-is-an-internet-connecti):
# 1. get $PROJECT_DIR and $RASPBERRY_PI_USER from the .env file
#    export $(cat /path/to/.env | xargs)
# 2. run this file
#    bash -c "${PROJECT_DIR}/scripts/raspberry_pi_on_startup.sh > /path/to/run.log 2>&1"

echo "-- INITIALIZING --"

# Pull any new changes
echo "** Pulling latest changes from bandcamp_suggestor"
say "Updating"
sudo "${PROJECT_DIR}bandcamp/bin/python3" "${PROJECT_DIR}scripts/wait_for_network.py"
sudo find "${PROJECT_DIR}.git/objects/" -size 0 -exec rm -f {} \; # Fixes git if broken
sudo -u $RASPBERRY_PI_USER -i git -C $PROJECT_DIR fetch origin # Fixes git if broken
sudo -u $RASPBERRY_PI_USER -i git -C $PROJECT_DIR pull origin main

# Run the script
echo "** Running bandcamp_suggestor"
say "Starting radio"
sudo "${PROJECT_DIR}bandcamp/bin/python3" "${PROJECT_DIR}scripts/play_recommendation.py" &
