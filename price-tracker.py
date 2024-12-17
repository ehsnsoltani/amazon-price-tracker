import selenium.common.exceptions
import urllib3.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import smtplib

# User email and password for sending price alert emails
email = ""
password = ""

# Get user input for the Amazon product URL and target price
url = input("Enter the Amazon product URL you want to track: ")
target_price = float(input("Enter your target price (numeric value only): "))

# Set up Chrome options
chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)

# Track captcha bypass attempts
attempts = 0


# Function to request the target URL and handle potential exceptions
def selenium_request(target_url):
    global attempts  # Access the global attempts variable

    try:
        driver.get(target_url)
        location_button = driver.find_element(By.ID, "nav-global-location-popover-link")
        location_button.click()

    except selenium.common.exceptions.NoSuchElementException:
        attempts += 1
        print(f"Attempting to bypass captcha ({attempts} attempt)")
        selenium_request(url)  # Retry if captcha encountered

    except urllib3.exceptions.ReadTimeoutError:
        print("Connection issue encountered. Retrying...")
        selenium_request(url)  # Retry on connection errors


# Function to change location on Amazon
def change_location():
    time.sleep(3)
    country_list = driver.find_element(By.ID, "GLUXCountryListDropdown")
    country_list.click()

    country_select = driver.find_element(By.ID, "GLUXCountryList_1")
    country_select.click()

    done_btn = driver.find_element(By.NAME, "glowDoneButton")
    done_btn.click()


# Request the product page, change location, and wait for page to load
selenium_request(url)
change_location()
time.sleep(5)

# Get the HTML source code of the product page
webpage_html = driver.page_source

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(webpage_html, "html.parser")

# Extract product title, price elements, and additional details
product_title = soup.select_one(selector="#productTitle")
price_element = soup.select_one(selector=".priceToPay")
feature_price = soup.select_one(selector="div#corePrice_feature_div .a-offscreen")
tooltip = soup.select_one(selector="ul.swatches")
product_status = soup.select_one(selector="#availability")

# Store product prices in a list to handle multiple options
product_prices_list = []

# Check for price based on available elements and logic
if price_element is not None:
    price = float(price_element.getText().replace(" ", "").replace("$", ""))
    product_prices_list.append(price)
elif feature_price is not None:
    price = float(feature_price.getText().replace(" ", "").replace("$", ""))
    product_prices_list.append(price)

elif tooltip is not None:
    # Extract price from tooltip content
    content_list = tooltip.getText().split(" ")
    for content in content_list:
        if "$" in content:
            product_prices_list.append(float(content.replace(" ", "").replace("$", "")))

else:  # No price information found
    if product_status is not None:
        product_text = product_status.getText()
        print(product_text)  # Display product status message
    else:
        print("Something went wrong. Please try again.")

# Check if any price in the list is lower than the target price
for item_price in product_prices_list:
    print(f"Current price: ${item_price}")
    if item_price <= target_price:
        # Send email alert if a price meets the target
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=email, password=password)
            connection.sendmail(
                from_addr=email,
                to_addrs="Email Address",
                msg=f"Subject:Price Alert\n\n{product_title.getText()} with price ${item_price} is lower than your target price\n\nproduct link: {url}"
            )
        print("Email Successfully Sent")
        break
