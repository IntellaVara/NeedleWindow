from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

def count_tabs_and_windows():
    # Set up the Selenium WebDriver
    driver = webdriver.Firefox()

    # Open a few sample tabs for demonstration
    driver.get("http://example.com")
    driver.execute_script("window.open('http://example.org')")
    driver.execute_script("window.open('http://example.net')")

    # Wait a bit for all tabs to open
    time.sleep(2)

    # Get all window handles
    window_handles = driver.window_handles
    print(f"Total windows: {len(window_handles)}")

    # Count tabs in each window
    for window_handle in window_handles:
        driver.switch_to.window(window_handle)
        # In Selenium, each window handle typically corresponds to one window with multiple tabs
        # Selenium views each tab as a window, so here we print out each tab
        tabs = driver.window_handles  # Refresh handles in the current window context
        print(f"Window {window_handle} has {len(tabs)} tabs")

    driver.quit()

count_tabs_and_windows()
