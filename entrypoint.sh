#!/bin/bash
set -e

# If the first arg is "daemon", run the loop
if [ "$1" = "daemon" ]; then
    echo "Starting AWS-Brief in DAEMON mode (Interval: ${SCAN_INTERVAL:-900}s)..."
    
    # Init DB once
    python main.py init-db
    
    while true; do
        echo "[$(date)] Running Process Cycle..."
        # Capture exit code so script doesn't die on temporary python error
        python main.py process-cycle || echo "Cycle failed, retrying next time."
        
        echo "Sleeping for ${SCAN_INTERVAL:-900} seconds..."
        sleep ${SCAN_INTERVAL:-900}
    done
else
    # Otherwise pass arguments to python main.py
    exec python main.py "$@"
fi
