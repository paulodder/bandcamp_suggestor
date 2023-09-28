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
sudo ${PROJECT_DIR}bandcamp/bin/python3 ${PROJECT_DIR}scripts/wait_for_network.py

# Run the script
echo "** Running bandcamp_suggestor"
# say "Starting radio"
sudo "${PROJECT_DIR}bandcamp/bin/python3" "${PROJECT_DIR}scripts/play_infinite_radio.py" &

# To stop the radio from ssh:
# ps ax | grep bandcamp_suggestor to find the process_id
# sudo kill <process_id>
