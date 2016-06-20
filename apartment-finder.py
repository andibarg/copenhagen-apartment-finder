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

TARGET_EMAIL = 'EDIT ME' # Where the new apartments should be sent

DBA_URL = 'EDIT ME' # For example, http://www.dba.dk/boliger/andelsbolig/andelslejligheder/vaerelser-3/?soeg=andelsbolig&vaerelser=4&vaerelser=5&vaerelser=6&boligarealkvm=(70-)&sort=listingdate-desc&pris=(1500000-2499999)&pris=(1000000-1499999)&soegfra=1060&radius=5
BOLIGA_URL = 'EDIT ME' # For example, http://www.boliga.dk/soeg/resultater/a194d60c-e272-4c09-a7fd-899763577c58?sort=liggetid-a')


class User(object):
    def __init__(self, email, dba_url, boliga_url=None):
        self.email = email
        self.dba_url = dba_url
        self.boliga_url = boliga_url
        self.seen_urls = set()
        self.first_run = True

def send_email(headline, url, recipient):
    smtp_obj = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Change if not using gmail
    smtp_obj.login(GMAIL_USER, GMAIL_PASSWORD)
    FROM = GMAIL_USER
    TO = [recipient] #must be a list
    SUBJECT = headline
    TEXT = url
    
    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    smtp_obj.sendmail(FROM, TO, message)
    smtp_obj.close()

def crawl_dba(user):
    session = requests.Session()
    session.encoding = 'utf-8'
    r = session.get(user.dba_url)
    soup = BeautifulSoup(r.text, convertEntities=BeautifulSoup.HTML_ENTITIES)
    listings = soup.findAll('tr', 'dbaListing')
    for listing in listings:
        a = listing.findAll('a', 'listingLink')[1]
        link = a['href'].encode('utf-8')
        headline = a.contents[0].encode('utf-8')
        if headline is None:
            headline = link
        process_property(headline, link, user)

def crawl_boliga(user):
    session = requests.Session()
    session.encoding = 'utf-8'
    r = session.get(user.boliga_url)
    soup = BeautifulSoup(r.text.encode('utf-8'), convertEntities=BeautifulSoup.HTML_ENTITIES)
    listings = soup.findAll('tr', 'pRow')
    for listing in listings:
        link_element = listing.findAll('a')[1]
        headline = link_element['title'].encode('utf-8')
        url = ('http://www.boliga.dk' + link_element['href']).encode('utf-8')
        process_property(headline, url, user)

def process_property(headline, url, user):
    if url not in user.seen_urls:
        if not user.first_run:
            send_email(headline, url, user.email)
        user.seen_urls.add(url)
        print 'Property found: %s - %s' % (headline, url)

def main():
    user = User(email=TARGET_EMAIL,
                dba_url=DBA_URL,
                boliga_url=BOLIGA_URL)

    while True:
        try:
            crawl_dba(user)
            crawl_boliga(user)
            if user.first_run:
                print 'First run passed and fetched %d properties' % len(user.seen_urls)
                user.first_run = False
            time.sleep(REFRESH_INTERVAL_SECONDS)
        except Exception as e:
            print e

main()
