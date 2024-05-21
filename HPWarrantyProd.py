import subprocess
import sys
import os
import datetime
import time

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Installs selenium for Edge & Chrome as failover
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    install('selenium')
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

import winreg as reg

# Function to check if the manufacturer is HP
def is_hp():
    try:
        reg_key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"PATH\TO\YOUR\MANUFACTURER\KEY")
        manufacturer, _ = reg.QueryValueEx(reg_key, "Manufacturer")
        reg.CloseKey(reg_key)
        return 'hp' in manufacturer.lower()
    except WindowsError as e:
        print(f"Failed to read Manufacturer from registry: {e}")
        return False
if not is_hp():
    print("This script is designed to run on HP machines only.")
    sys.exit()

# Get the serial number of the PC from the registry
try:
    reg_key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"PATH\TO\YOUR\SERIAL\NUMBER")
    serial_number, _ = reg.QueryValueEx(reg_key, "SerialNumber")
    reg.CloseKey(reg_key)
except WindowsError as e:
    print(f"Failed to read SerialNumber from registry: {e}")
    sys.exit()

# Set up Edge in headless mode with suppressed logging
edge_options = EdgeOptions()
edge_options.add_argument("--headless") # Comment this line to see GUI interactions
edge_options.add_argument("--disable-gpu")
edge_options.add_argument("--no-sandbox")
edge_options.add_argument("--disable-dev-shm-usage")
edge_options.add_argument("--log-level=3") # Comment this line to unsupress logging

# Set up Chrome in headless mode with suppressed logging as fallback
chrome_options = ChromeOptions()
chrome_options.add_argument("--headless") # Comment this line to see GUI interactions
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3") # Comment this line to unsupress logging

# Attempt to use Edge driver first, fallback to Chrome if it fails
retry_attempts = 3
driver = None

for attempt in range(retry_attempts):
    try:
        driver = webdriver.Edge(options=edge_options)
        break
    except Exception as e:
        print(f"Edge WebDriver failed to initialize: {e}. Retrying with Chrome...")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            break
        except Exception as e:
            print(f"Chrome WebDriver failed to initialize: {e}. Retrying... ({attempt + 1}/{retry_attempts})")
            time.sleep(2)
else:
    print("Failed to initialize WebDriver. Exiting.")
    sys.exit()

# Navigate to the warranty check page
driver.get("https://support.hp.com/au-en/checkwarranty")

# Wait for the page to fully load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'inputtextpfinder')))

# Finds Element needed
def find_element_with_retries(by, value, retries=5, delay=2):
    for attempt in range(retries):
        try:
            element = driver.find_element(by, value)
            return element
        except Exception as e:
            print(f"Element not found: {e}. Retrying... ({attempt + 1}/{retries})")
            time.sleep(delay)
    raise Exception(f"Failed to find element by {by} with value {value} after {retries} attempts")

# Fill the form and submit
input_element = find_element_with_retries(By.ID, 'inputtextpfinder')
input_element.send_keys(serial_number)
submit_button = find_element_with_retries(By.ID, 'FindMyProduct')
submit_button.click()

# Handle potential privacy policy acceptance
wait = WebDriverWait(driver, 10)
try:
    privacy_accept_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
    privacy_accept_button.click()
except:
    print("No privacy policy button found or not clickable.")

# Check if 'product-number inputtextPN' field appears
try:
    product_number_field = wait.until(EC.presence_of_element_located((By.ID, 'product-number inputtextPN')))
    # If the field appears, get the ProductNumber from the registry
    try:
        reg_key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"PATH\TO\YOUR\PRODUCT\NUMBER")
        product_number, _ = reg.QueryValueEx(reg_key, "ProductNumber")
        reg.CloseKey(reg_key)
    except WindowsError as e:
        print(f"Failed to read ProductNumber from registry: {e}")
        driver.quit()
        sys.exit()

    # Fill the 'product-number inputtextPN' field and resubmit
    product_number_field.send_keys(product_number)
    resubmit_button = find_element_with_retries(By.ID, 'FindMyProductNumber')
    resubmit_button.click()
except:
    print("Product number field not found. Continuing...")

# Wait for the warranty end date to load
try:
    warranty_end_date_text = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//div[contains(@class, 'info-item')]//div[contains(text(), 'End date')]/following-sibling::div"))).text
except Exception as e:
    print(f"Failed to retrieve warranty end date: {e}")
    driver.quit()
    sys.exit()

# Parse the date from the format 'May 23, 2025' to 'YYYY-MM-DD'
parsed_date = datetime.datetime.strptime(warranty_end_date_text, '%B %d, %Y')
formatted_date = parsed_date.strftime('%Y-%m-%d')

# Save the formatted warranty end date to a registry key
def set_reg(name, value):
    try:
        reg_path = r"SOFTWARE\\CIT\\Warranty"
        key = reg.CreateKey(reg.HKEY_LOCAL_MACHINE, reg_path)
        reg.SetValueEx(key, name, 0, reg.REG_SZ, value)
        reg.CloseKey(key)
        return True
    except WindowsError:
        return False

set_reg("WarrantyEndDate", formatted_date)

driver.quit()  # Clean up by closing the browser

# Output to confirm
print("Warranty end date saved to registry.")
