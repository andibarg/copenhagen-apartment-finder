#!/usr/bin/python

# -*- coding: utf-8 -*-

import time
import smtplib
import urllib.request
import yaml
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

class Watcher(object):
    def __init__(self, data):
        self.name = data.get('name')
        self.boliga_url = data.get('boliga_url')
        self.dba_url = data.get('dba_url')
        self.gmail_sender = data.get('gmail_sender')
        self.gmail_password = data.get('gmail_password')
        self.email_recipients = data.get('email_recipients')
        self.should_bcc_recipients = data.get('should_bcc_recipients', False)
        self.trigger_emails_on_first_run = data.get('trigger_emails_on_first_run', False)
        self.seen_urls = set()
        self.first_run = True

def send_email(headline, url, watcher):
    smtp_obj = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Change if not using gmail
    smtp_obj.login(watcher.gmail_sender, watcher.gmail_password)

    # Prepare actual message
    body = "%s\r\n\r\n%s" % (url,headline)
    msg = MIMEText(body.encode('utf-8'), _charset='utf-8')
    msg['Subject'] = watcher.name
    msg['From'] = watcher.gmail_sender
    if not watcher.should_bcc_recipients:
        msg['To'] = ', '.join(watcher.email_recipients)

    # Sending email
    smtp_obj.sendmail(watcher.gmail_sender, watcher.email_recipients, msg.as_string())
    smtp_obj.close()

def crawl_dba(watcher):
    # Query website and get html
    html_doc = urllib.request.urlopen(watcher.dba_url)
    soup = BeautifulSoup(html_doc,'html.parser')
    listings = soup.findAll('tr', 'dbaListing')
    for listing in listings:
        a = listing.findAll('a', 'listingLink')[1]
        link = a['href']
        headline = a.contents[0]
        if headline is None:
            headline = link
        process_property(headline, link, watcher)

def crawl_boliga(watcher):
    html_doc = urllib.request.urlopen(watcher.boliga_url)
    soup = BeautifulSoup(html_doc, 'html.parser')
    listings = soup.findAll('div', 'body')
    for listing in listings:
        link_element = listing.find('a')
        headline = link_element.get_text()
        url = ('https://www.selvsalg.dk' + link_element.get('href'))
        process_property(headline, url, watcher)

def process_property(headline, url, watcher):
    if url not in watcher.seen_urls:
        if not watcher.first_run or watcher.trigger_emails_on_first_run:
            send_email(headline, url, watcher)
        watcher.seen_urls.add(url)
        print('%s -> Item found: %s' % (watcher.name, url))

def main():
    config_filename = "config.yaml"
    with open(config_filename, 'r') as config_data:
        try:
            config = yaml.load(config_data)
        except yaml.YAMLError as e:
            print(e)
            raise SystemExit('Unable to open config file %s: ERROR: %s' % (config_filename, e))

    refresh_interval = config.get('refresh_interval_seconds', 600)
    watchers = [Watcher(watcher) for watcher in config['watchers']]

    while True:
        try:
            for watcher in watchers:
                crawl_boliga(watcher)
                crawl_dba(watcher)
                if watcher.first_run:
                    watcher.first_run = False
                print('Waiting ...')
            time.sleep(refresh_interval)
        except Exception as e:
            print(e)

main()
