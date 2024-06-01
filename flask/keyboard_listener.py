from pynput import keyboard
import requests

def on_activate_h():
    print("Ctrl+Shift+H pressed, triggering Flask action.")
    url = 'http://localhost:5000/hello'  # Endpoint for a simple Hello World action
    response = requests.get(url)
    print(f'Response from Flask: {response.text}')

    url = 'http://localhost:5000/request_tabs'  # Endpoint to request tab information
    response = requests.get(url)
    print(f'Response from Flask: {response.text}')
    
    # Request to activate the first tab and focus the window
    url = 'http://localhost:5000/activate_first_tab'
    response = requests.get(url)
    print(f'Response from Flask: {response.text}')


def for_canonical(f):
    return lambda k: f(l.canonical(k))

# Define your shortcut key combination here
hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<shift>+h'),
    on_activate_h
)

# The event listener will be running in this block
with keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)) as l:
    l.join()
