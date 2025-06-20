import time
import json
import os
import signal
import sys
import random
import traceback
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

import database
from database import Database

WEBSITES = [
    # websites of your choice
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

TRACES_PER_SITE = 1000
FINGERPRINTING_URL = "http://localhost:5000" 
OUTPUT_PATH = "dataset.json"

# Initialize the database to save trace data reliably
database.db = Database(WEBSITES)

""" Signal handler to ensure data is saved before quitting. """
def signal_handler(sig, frame):
    print("\nReceived termination signal. Exiting gracefully...")
    try:
        database.db.export_to_json(OUTPUT_PATH)
    except:
        pass
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


"""
Some helper functions to make your life easier.
"""

def is_server_running(host='127.0.0.1', port=5000):
    """Check if the Flask server is running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def setup_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")  # Optional, but helpful for some environments

    # Update this path to your actual chromedriver.exe location
    CHROMEDRIVER_PATH = r"C:\Users\alami\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=chrome_options)


def retrieve_traces_from_backend(driver):
    """Retrieve traces from the backend API."""
    traces = driver.execute_script("""
        return fetch('/api/get_results')
            .then(response => response.ok ? response.json() : {traces: []})
            .then(data => data.traces || [])
            .catch(() => []);
    """)
    
    count = len(traces) if traces else 0
    print(f"  - Retrieved {count} traces from backend API" if count else "  - No traces found in backend storage")
    return traces or []

def clear_trace_results(driver, wait):
    """Clear all results from the backend by pressing the button."""
    clear_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear all results')]")
    clear_button.click()

    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, "//div[@role='alert']"), "Cleared"))
    
def is_collection_complete():
    """Check if target number of traces have been collected."""
    current_counts = database.db.get_traces_collected()
    remaining_counts = {website: max(0, TRACES_PER_SITE - count) 
                      for website, count in current_counts.items()}
    return sum(remaining_counts.values()) == 0

"""
Your implementation starts here.
"""

def collect_single_trace(driver, wait, website_url):
    """Collect a single trace for a target website."""
    try:
        # Open fingerprinting page in first tab
        driver.get(FINGERPRINTING_URL)
        
        # Open target website in new tab
        driver.switch_to.new_window('tab')
        driver.get(website_url)
        
        # Simulate user activity (scroll 3 times)
        body = driver.find_element(By.TAG_NAME, 'body')
        for _ in range(3):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(random.uniform(0.5, 1.5))
        
        # Switch back to fingerprinting tab
        driver.switch_to.window(driver.window_handles[0])
        
        # Trigger trace collection
        collect_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Collect Trace')]")))
        collect_button.click()
        
        # Wait for collection complete
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element(
                (By.XPATH, "//div[@role='alert']"), "Trace collected"))

        # Get trace directly from backend using JavaScript
        trace = driver.execute_script("""
            return fetch('/download_traces')
                .then(r => r.ok ? r.json() : [])
                .then(data => data.length > 0 ? data[data.length-1] : null)
                .catch(() => null)
        """)
        
        # Close target website tab
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        return trace

    except Exception as e:
        print(f"Error collecting trace: {str(e)}")
        traceback.print_exc()
        return None




def collect_fingerprints(driver, target_counts=None):
    """Collect fingerprints until target counts are reached."""
    if target_counts is None:
        target_counts = {site: TRACES_PER_SITE for site in WEBSITES}
    
    current_counts = database.db.get_traces_collected()
    remaining = {
        site: max(0, target_counts[site] - current_counts.get(site, 0))
        for site in WEBSITES
    }
    
    new_traces = 0
    for website in WEBSITES:
        while remaining[website] > 0:
            print(f"Collecting trace {TRACES_PER_SITE - remaining[website] + 1}/{TRACES_PER_SITE} for {website}")
            trace = collect_single_trace(driver, WebDriverWait(driver, 30), website)
            if trace:
                database.db.save_trace(website, WEBSITES.index(website), trace)
                remaining[website] -= 1
                new_traces += 1
                time.sleep(2)  # Cool-down period
            else:
                print(f"Failed to collect trace for {website}. Retrying...")
                time.sleep(5)
    return new_traces



def main():
    """Main automation loop."""
    if not is_server_running():
        print("Error: Flask server not running. Start it first!")
        return
    
    database.db.init_database()
    driver = setup_webdriver()
    
    try:
        print("Starting automated data collection...")
        driver.get(FINGERPRINTING_URL)
        
        while not is_collection_complete():
            collected = collect_fingerprints(driver)
            print(f"Collected {collected} new traces in this batch")
            
            if collected == 0:
                print("No new traces collected. Retrying...")
                time.sleep(10)
                
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        
    finally:
        print("Shutting down...")
        driver.quit()
        database.db.export_to_json(OUTPUT_PATH)
        print(f"Data exported to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
