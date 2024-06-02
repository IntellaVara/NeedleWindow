import tkinter as tk
from tkinter import simpledialog
from pynput import keyboard
import requests



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


# def on_activate_h():

#     # Pop up the input dialog to get the user's query
#     user_query = get_user_query()

#     print("Ctrl+Shift+H pressed, triggering Flask action.")
#     url = 'http://localhost:5000/hello'  # Endpoint for a simple Hello World action
#     response = requests.get(url)
#     print(f'Response from Flask: {response.text}')

#     url = 'http://localhost:5000/request_tabs'  # Endpoint to request tab information
#     response = requests.get(url)
#     print(f'Response from Flask: {response.text}')
    
#     # Request to activate the first tab and focus the window
#     url = 'http://localhost:5000/activate_first_tab'
#     response = requests.get(url)
#     print(f'Response from Flask: {response.text}')


def for_canonical(f):
    return lambda k: f(l.canonical(k))

# Define your shortcut key combination here
hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<shift>+k'),
    on_activate_h
)

# The event listener will be running in this block
with keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)) as l:
    l.join()
