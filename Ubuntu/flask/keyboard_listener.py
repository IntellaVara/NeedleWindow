import tkinter as tk
from tkinter import simpledialog
from pynput import keyboard
import requests
import sys


# Function to display the input dialog and return the user input
def get_user_query():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    query = simpledialog.askstring("Input", "Enter your query:", parent=root)
    root.destroy()  # Destroy the root window after input
    return query


def on_activate_h():
    user_query = get_user_query()
    if user_query:
        url = 'http://localhost:5000/find_matching_tab'
        response = requests.post(url, json={"query": user_query})
        print(f'Response from Flask: {response.text}')



def format_hotkey(hotkey_str):
    """Formats the hotkey string to match pynput's expected format."""
    # Splitting the input into parts and formatting correctly
    parts = hotkey_str.split('+')
    formatted_parts = []
    for part in parts:
        part = part.strip().lower()  # Normalize the input
        if part in ['ctrl', 'shift', 'alt', 'cmd']:
            formatted_parts.append(f'<{part}>')  # Special keys
        else:
            formatted_parts.append(part)  # Regular keys like letters or numbers
    return '+'.join(formatted_parts)

def for_canonical(f):
    """Converts a function to work with canonical key values."""
    return lambda k: f(l.canonical(k))


def main(hotkey_str):
    formatted_hotkey = format_hotkey(hotkey_str)  # Ensure hotkey is correctly formatted
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse(formatted_hotkey),
        on_activate_h
    )
    
    # Define the canonical wrapper within main to have access to 'listener'
    def for_canonical(f):
        return lambda k: f(listener.canonical(k))
    
    # Event listener setup with the canonical wrapper
    with keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)) as listener:
        listener.join()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("No hotkey specified, using default 'ctrl+shift+k'.")
        main('ctrl+shift+k')
