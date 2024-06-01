from flask import Flask
from flask_socketio import SocketIO, emit
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client Connected')
    emit('server_response', {'message': 'Hello from Flask!'})
    

@socketio.on('disconnect')
def handle_disconnect():
    print('Client Disconnected')
    try:
        # Perform necessary cleanup
        print('Performed cleanup after disconnection.')
    except Exception as e:
        print(f'Error during disconnect: {str(e)}')


@socketio.on('client_message')
def handle_client_message(message):
    print('Received message from client:', message)
    emit('server_response', {'message': 'Received your message: ' + str(message)})

@app.route('/hello')
def hello_world():
    print("Hello World triggered from shortcut")
    return "Hello World response from flask!"

@app.route('/request_tabs')
def request_tabs():
    print("Request for tabs triggered by shortcut")
    emit('request_tabs', {'message': 'Please send tabs'}, namespace='/', broadcast=True)
    return "Requested tabs from extension"

@socketio.on('send_tabs')
def handle_send_tabs(data):
    print("Received tabs from the extension:")
    if 'windowId' in data:
        print(f"Window ID: {data['windowId']}")



@app.route('/activate_first_tab')
def activate_first_tab():
    # Emit an event to the extension to activate the first tab and focus the window
    emit('activate_first_tab', {'message': 'Activate first tab and focus window'}, namespace='/', broadcast=True)
    return "Command to activate first tab and focus window sent."

@socketio.on('window_info')
def handle_window_info(data):
    print("Received window info:", data)
    window_id = data['windowId']  # Assuming the window ID is directly usable
    print(f"Window ID is {window_id}")
    if 'title' in data:
        result = focus_firefox_window_by_title(data['title'])
        print(result)
   



def focus_firefox_window_by_title(title_from_extension):
    try:
        # Retrieve all Firefox windows with their titles
        output = subprocess.check_output(
            "xdotool search --onlyvisible --class 'firefox' | xargs -I % sh -c 'echo \"%,$(xdotool getwindowname %)\"'",
            shell=True
        ).decode()
        
        # Process the output to find a matching window
        for line in output.splitlines():
            window_id, window_title = line.split(",", 1)
            # Check if the window title from extension matches the one retrieved by xdotool
            if title_from_extension in window_title:
                print(f"Matching window found: {window_id}, focusing now.")
                subprocess.run(['xdotool', 'windowactivate', window_id])
                return f"Focused window with ID: {window_id}"
        return "No matching window found."
    except subprocess.CalledProcessError as e:
        return f"Failed to execute xdotool command: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500



if __name__ == '__main__':
    socketio.run(app, debug=True)
