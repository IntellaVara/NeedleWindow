#!/bin/bash

# Function to handle process termination
cleanup() {
    echo "Stopping Flask app and optional keyboard listener..."
    kill $FLASK_PID
    if [[ -n "$KEYBOARD_LISTENER_PID" ]]; then
        pkill -P $KEYBOARD_LISTENER_PID
    fi
    exit
}

# Trap signals to cleanup processes
trap cleanup SIGINT SIGTERM

# Prompt for GPU usage
read -p "Use GPU? (y/n): " use_gpu
use_gpu=$(echo "$use_gpu" | tr '[:upper:]' '[:lower:]')  # Convert to lowercase
gpu_flag=""
if [[ "$use_gpu" == "y" ]]; then
    gpu_flag="--cuda"
fi

# Prompt for interaction mode
read -p "Use hotkeys or persistent GUI? (Hotkeys/GUI, default GUI): " interaction_mode
interaction_mode=${interaction_mode:-GUI}
interaction_mode=$(echo "$interaction_mode" | tr '[:upper:]' '[:lower:]')  # Convert to lowercase
gui_flag=""
if [[ "$interaction_mode" == "gui" ]]; then
    gui_flag="--gui"
fi

KEYBOARD_LISTENER_PID="None" # Initialize as empty

# Conditionally start the keyboard listener if hotkeys mode is chosen
if [[ "$interaction_mode" == "hotkeys" ]]; then
    read -p "Type your preferred hotkey combination (Press Enter for default: ctrl+shift+k): " hotkey
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        gnome-terminal --tab -- bash -c "python keyboard_listener.py $hotkey; exec bash" &
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e "tell application \"Terminal\" to do script \"python keyboard_listener.py $hotkey\""
    fi
    KEYBOARD_LISTENER_PID=$!
    echo "Keyboard listener started with PID $KEYBOARD_LISTENER_PID"
fi

# Start the Flask app in the background with GPU option and interaction mode if specified
python app.py $gpu_flag $gui_flag --keyboard_listener_pid $KEYBOARD_LISTENER_PID &
FLASK_PID=$!
echo "Flask app started with PID $FLASK_PID"


# Wait for the Flask process to exit
wait $FLASK_PID
