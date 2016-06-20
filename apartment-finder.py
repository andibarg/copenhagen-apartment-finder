#!/usr/bin/python

# -*- coding: utf-8 -*-

import time
import smtplib
import requests
from BeautifulSoup import BeautifulSoup

REFRESH_INTERVAL_SECONDS = 30
GMAIL_USER = 'EDIT_ME' # The emails originate from here
# Note - when using gmail from an external app, you need to generate an app-specific password
# See https://support.google.com/mail/answer/1173270?hl=en
GMAIL_PASSWORD = 'EDIT ME'

TARGET_EMAILS = [
    'EDIT ME' # Where the new apartments should be sent
]
BCC_TARGETS = True # Whether or not the recipients should be bcc'ed

DBA_URL = 'EDIT ME' # For example, http://www.dba.dk/boliger/andelsbolig/andelslejligheder/vaerelser-3/?soeg=andelsbolig&vaerelser=4&vaerelser=5&vaerelser=6&boligarealkvm=(70-)&sort=listingdate-desc&pris=(1500000-2499999)&pris=(1000000-1499999)&soegfra=1060&radius=5
BOLIGA_URL = 'EDIT ME' # For example, http://www.boliga.dk/soeg/resultater/a194d60c-e272-4c09-a7fd-899763577c58?sort=liggetid-a')


class Watcher(object):
    def __init__(self, email_recipients, dba_url, boliga_url=None, bcc_recipients=False):
        self.email_recipients = email_recipients
        self.bcc_recipients = bcc_recipients
        self.dba_url = dba_url
        self.boliga_url = boliga_url
        self.seen_urls = set()
        self.first_run = True

def send_email(headline, url, recipients, bcc):
    smtp_obj = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Change if not using gmail
    smtp_obj.login(GMAIL_USER, GMAIL_PASSWORD)
    FROM = GMAIL_USER
    TO = recipients
    SUBJECT = headline
    TEXT = url
    
    # Prepare actual message
    message = "From: %s\r\n" % FROM
    if not bcc:
        message += "To: %s\r\n" % ", ".join(TO)
    message += "Subject: %s\r\n" % SUBJECT
    message += "\r\n"
    message += TEXT
    smtp_obj.sendmail(FROM, TO, message)
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
            send_email(headline, url, watcher.email_recipients, watcher.bcc_recipients)
        watcher.seen_urls.add(url)
        print 'Property found: %s - %s' % (headline, url)

def main():
    watcher = Watcher(
        email_recipients=TARGET_EMAILS,
        dba_url=DBA_URL,
        boliga_url=BOLIGA_URL,
        bcc_recipients=BCC_TARGETS
    )

    while True:
        try:
            crawl_dba(watcher)
            crawl_boliga(watcher)
            if watcher.first_run:
                print 'First run passed and fetched %d properties' % len(watcher.seen_urls)
                watcher.first_run = False
            time.sleep(REFRESH_INTERVAL_SECONDS)
        except Exception as e:
            print e

main()
