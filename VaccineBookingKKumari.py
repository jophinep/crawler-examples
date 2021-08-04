"""
Lambda function for vaccine crawler
"""

import os
import time
from datetime import date
from glob import glob

import boto3
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

SECONDS_TO_WAIT = 3
URL = 'https://bookmyvaccine.kumaricovidcare.in'
TODAY = date.today()
OUTFILE = f".vaccine_{TODAY}.txt"


def get_old_files():
    """Get old files"""
    try:
        files = []
        files = glob(".vaccine_*.txt")
        files.remove(OUTFILE)
    except ValueError:
        pass
    return files

def delete_old_files():
    """Delete old files"""

    deleted_count = 0
    for filename in get_old_files():
        try:
            os.remove(filename)
        except OSError:
            print(f"Error deleting file {filename}")
            continue
        deleted_count += 1
    print(f"{deleted_count} file{'s' if deleted_count != 1 else ''} deleted")


def crawl():
    """The actual crawler"""
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options, executable_path="./geckodriver")
    browser.get(URL)

    time.sleep(SECONDS_TO_WAIT)  # this need because results captured using ajax with jwt tokens

    elements = browser.find_elements_by_xpath("//button[contains(@class,'availability-btn')]")

    vaccine_data = []

    for e in elements:
        vaccine = e.find_element_by_xpath("preceding-sibling::p").text
        qty = 0 if e.text == 'Not Available' else int(e.text)
        vaccine_data.append({'vaccine_name': vaccine, 'quantity': qty, 'time': int(time.time())})

    return vaccine_data

def publish_result(vaccine_data):
    """
    Publish vaccine_data to SNS topic
    """
    topic_arn = os.environ["VACCINE_TOPIC"]
    sns = boto3.resource('sns')
    topic = sns.Topic(topic_arn)
    message = "\n".join([
        f"{vax['vaccine_name']}: {vax['quantity']} Available Now"
        for vax in vaccine_data if vax['quantity'] > 0
    ])
    print("Vaccine message")
    print(message)
    if message:
        topic.publish(Message=f"Hurry Up!\n\n{message}")
        with open(OUTFILE, "w") as outfile:
            outfile.write(message)

def vaccine_crawler(*args):
    if os.path.isfile(OUTFILE):
        print("Already notified today")
        return
    vaccine_data = crawl()
    publish_result(vaccine_data)

if __name__ == "__main__":
    delete_old_files()
    vaccine_crawler()

