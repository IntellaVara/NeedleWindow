#!/bin/bash

# Function to handle process termination
cleanup() {
    echo "Stopping Flask app and keyboard listener..."
    kill $FLASK_PID
    pkill -P $KEYBOARD_LISTENER_PID
    exit
}

# Trap signals to cleanup processes
trap cleanup SIGINT SIGTERM

# Start the Flask app in the background
python run.py &
FLASK_PID=$!
echo "Flask app started with PID $FLASK_PID"

# Start the keyboard listener in a new terminal
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    gnome-terminal --tab -- bash -c 'python keyboard_listener.py; exec bash' &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e 'tell application "Terminal" to do script "python keyboard_listener.py"' &
fi
KEYBOARD_LISTENER_PID=$!
echo "Keyboard listener started with PID $KEYBOARD_LISTENER_PID"

# Wait for the Flask process to exit
wait $FLASK_PID
