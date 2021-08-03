"""
Lambda function for vaccine crawler
"""

import os
import time

import boto3
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

SECONDS_TO_WAIT = 3
URL = 'https://bookmyvaccine.kumaricovidcare.in'


def crawl():
    """The actual crawler"""
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options)
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
        topic.publish(Message=message)

def vaccine_crawler(*args):
    vaccine_data = crawl()
    publish_result(vaccine_data)
