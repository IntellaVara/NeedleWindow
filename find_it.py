


from pynput import keyboard

def on_activate_h():
    print("Hello World")

def for_canonical(f):
    return lambda k: f(l.canonical(k))

# Define the key combination
hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<shift>+h'),
    on_activate_h
)

# The event listener will be running in this block
with keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)) as l:
    l.join()







