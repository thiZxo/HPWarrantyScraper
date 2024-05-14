import subprocess
import sys
import os
import datetime

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import wmi
except ImportError:
    install('wmi')

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    install('selenium')

import winreg as reg

# Initialize WMI client
c = wmi.WMI()

# Check if its a HP Machine
def is_hp():
    for system in c.Win32_ComputerSystem():
        if 'hp' in system.Manufacturer.lower():
            return True
    return False

# Exit if not a HP machine
if not is_hp():
    print("This script is designed to run on HP machines only. Exiting now...")
    sys.exit()

# Get the serial number of the machine
serial_number = c.Win32_BIOS()[0].SerialNumber

# Set up Chromium in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disables GPU hardware acceleration
chrome_options.add_argument("--no-sandbox")  # Bypass OS security
chrome_options.add_argument("--disable-dev-shm-usage")  # Fix found for limited resource issues

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://support.hp.com/au-en/check-warranty")

# Fills in the Serialnumber field by ID, then presses 'Submit'
input_element = driver.find_element(By.ID, 'inputtextpfinder')
input_element.send_keys(serial_number)
driver.find_element(By.ID, 'FindMyProduct').click()

# If privacy policy appears, click 'I Accept'.
wait = WebDriverWait(driver, 10)
try:
    privacy_accept_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
    privacy_accept_button.click()
except:
    print("Privacy Policy skipped.")

# Wait for the warranty end date to load
warranty_end_date_text = wait.until(EC.visibility_of_element_located(
    (By.XPATH, "//div[contains(@class, 'info-item')]//div[contains(text(), 'End date')]/following-sibling::div"))).text

# Parse the date from the format 'May 23, 2025' to 'YYYY-MM-DD'
parsed_date = datetime.datetime.strptime(warranty_end_date_text, '%B %d, %Y')
formatted_date = parsed_date.strftime('%Y-%m-%d')

# Save the formatted warranty end date to a registry key
def set_reg(name, value):
    try:
        reg_path = r"YOUR/REGISTRY/PATH/HERE"
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
