#!/usr/bin/python

# -*- coding: utf-8 -*-

import time
import smtplib
import requests
import yaml
from BeautifulSoup import BeautifulSoup

class Watcher(object):
    def __init__(self, data):
        self.name = data.get('name')
        self.boliga_url = data.get('boliga_url')
        self.dba_url = data.get('dba_url')
        self.gmail_sender = data.get('gmail_sender')
        self.gmail_password = data.get('gmail_password')
        self.email_recipients = data.get('email_recipients')
        self.should_bcc_recipients = data.get('should_bcc_recipients', False)
        self.seen_urls = set()
        self.first_run = True

def send_email(headline, url, watcher):
    smtp_obj = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Change if not using gmail
    smtp_obj.login(watcher.gmail_sender, watcher.gmail_password)

    # Prepare actual message
    message = "From: %s\r\n" % watcher.gmail_sender
    if not watcher.should_bcc_recipients:
        message += "To: %s\r\n" % ", ".join(watcher.email_recipients)
    message += "Subject: %s\r\n" % headline
    message += "\r\n"
    message += url
    smtp_obj.sendmail(watcher.gmail_sender, watcher.email_recipients, message)
    smtp_obj.close()

def crawl_dba(watcher):
    session = requests.Session()
    session.encoding = 'utf-8'
    r = session.get(watcher.dba_url)
    soup = BeautifulSoup(r.text, convertEntities=BeautifulSoup.HTML_ENTITIES)
    listings = soup.findAll('tr', 'dbaListing')
    for listing in listings:
        a = listing.findAll('a', 'listingLink')[1]
        link = a['href'].encode('utf-8')
        headline = a.contents[0].encode('utf-8')
        if headline is None:
            headline = link
        process_property(headline, link, watcher)

def crawl_boliga(watcher):
    session = requests.Session()
    session.encoding = 'utf-8'
    r = session.get(watcher.boliga_url)
    soup = BeautifulSoup(r.text.encode('utf-8'), convertEntities=BeautifulSoup.HTML_ENTITIES)
    listings = soup.findAll('tr', 'pRow')
    for listing in listings:
        link_element = listing.findAll('a')[1]
        headline = link_element['title'].encode('utf-8')
        url = ('http://www.boliga.dk' + link_element['href']).encode('utf-8')
        process_property(headline, url, watcher)

def process_property(headline, url, watcher):
    if url not in watcher.seen_urls:
        if not watcher.first_run:
            send_email(headline, url, watcher)
        watcher.seen_urls.add(url)
        print '%s -> Property found: %s - %s' % (watcher.name, headline, url)

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
                    print '%s -> First run passed and fetched %d properties' % (watcher.name, len(watcher.seen_urls))
            time.sleep(refresh_interval)
        except Exception as e:
            print e

main()
