#!/usr/bin/env python

import os
import sys
import code
import json
import random
import pickle
import urllib3
import logging
import tempfile
import threading
import os.path as op
from collections import OrderedDict
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = 'client_secret.json'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # annoying as fok
# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly', 'https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

log = logging.getLogger()

pool_manager = urllib3.PoolManager()

def get_authenticated_service():
    credentials_path = op.join(op.dirname(sys.argv[0]), 'credentials.dat')
    if not op.exists(credentials_path):
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        credentials = flow.run_local_server()
        with open(credentials_path, 'wb') as credentials_dat: pickle.dump(credentials, credentials_dat)
    else:
        with open(credentials_path, 'rb') as credentials_dat:
            credentials = pickle.load(credentials_dat)
            if credentials.expired:
                credentials.refresh(Request())
                log.debug('Credentials refreshed.')
        with open(credentials_path, 'wb') as credentials_dat: pickle.dump(credentials, credentials_dat)
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def channels_list_by_username(service, **kwargs):
    results = service.channels().list(**kwargs).execute()
    log.debug('This channel\'s ID is %s. Its title is %s, and it has %s views.' %
             (results['items'][0]['id'],
                results['items'][0]['snippet']['title'],
                results['items'][0]['statistics']['viewCount']))

def search(keyword, **kwargs):
    service = get_authenticated_service()
    vids_dict = service.search().list(q=keyword,**kwargs).execute()
    search_results = []
    for v_ix,i in enumerate(vids_dict['items']):
        try:
            if 'videoId' in i['id']:
                vid_link = 'https://youtube.com/watch?v=' + i['id']['videoId']
                tf = tempfile.NamedTemporaryFile(delete=False)
                vid_snippet = i['snippet']
                img_url = vid_snippet['thumbnails']['high']['url']
                vid_title = vid_snippet['title']
                search_results.append({'lnk': vid_link, 'ttl': vid_title, 'tf': tf.name})
                img_download_threads.append(threading.Thread(target=download_image, args=[tf,img_url]))
        except Exception as e: log.debug(e)
    return search_results

def download_image(tf, url):
    tf.write(pool_manager.request('GET', url, preload_content=False).read())
    tf.close()

def get_front_page(ccount, vcount):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()
    log.debug('Authenticated')
    subs_dict = service.subscriptions().list(part='id,snippet', maxResults=ccount, mine=True).execute()
    subs = subs_dict['items']
    front_page = OrderedDict()
    for sub_ix,i in enumerate(subs):
        channel_snippet = i['snippet']
        channel_id = channel_snippet['resourceId']['channelId']
        channel_title = channel_snippet['title']
        response = service.search().list(part='snippet', maxResults=vcount, channelId=channel_id, order='date', type='').execute()
        channel_vids = []
        img_download_threads = []
        for vid_ix,cv in enumerate(response['items']):
            try:
                if 'videoId' in cv['id']:
                    vid_link = 'https://youtube.com/watch?v=' + cv['id']['videoId']
                    tf = tempfile.NamedTemporaryFile(delete=False)
                    vid_snippet = cv['snippet']
                    img_url = vid_snippet['thumbnails']['high']['url']
                    vid_title = vid_snippet['title']
                    channel_vids.append({'lnk': vid_link, 'ttl': vid_title, 'tf': tf.name})
                    img_download_threads.append(threading.Thread(target=download_image, args=[tf,img_url]))
#             except: pass
            except: raise
        for t in img_download_threads: t.start()
        front_page[channel_title] = channel_vids
    keys = list(front_page)
    random.shuffle(keys)
    for key in keys: front_page.move_to_end(key)
    return front_page

def get_home_page():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()
    log.debug('Authenticated')
    subs_dict = service.activities().list(part='snippet', maxResults=25, home=True,).execute()
    return subs_dict

if __name__ == '__main__':
    results = search('kek', part='snippet')
    code.interact(local=locals())
