#!/usr/bin/env python

import os
import sys
import code
import random
import pickle
import urllib3
import logging
import datetime
import tempfile
import threading
import os.path as op
from collections import OrderedDict
from googleapiclient.discovery import build
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

def search(keyword, vcount, **kwargs):
    service = get_authenticated_service()
    subs_dict = service.search().list(part='id, snippet', q=keyword, maxResults=vcount).execute()
    subs = subs_dict['items']
    results = OrderedDict()
    for sub_ix,i in enumerate(subs):
        vid_snippet = i['snippet']
        channel_title = i['snippet']['channelTitle']
        img_download_threads = []
        channel_vids = []
        try:
            vid = {}
            vid['id'] = i['id']['videoId']
            vid['lnk'] = 'https://youtube.com/watch?v=' + vid['id']  
            vid['stats'] = get_authenticated_service().videos().list(part='statistics', id=vid['id']).execute()
            vid['ttl'] = html_decode(vid_snippet['title'])
            vid['dsc']  = html_decode(vid_snippet['description'])
            vid['dat']   = datetime.datetime.strptime(vid_snippet['publishedAt'].replace('.000Z', ''), '%Y-%m-%dT%H:%M:%S')
            tf = tempfile.NamedTemporaryFile(delete=False)
            vid['tf'] = tf.name
            img_url = vid_snippet['thumbnails']['high']['url']
            img_download_threads.append(threading.Thread(target=download_image, args=[tf,img_url]))
            channel_vids.append(vid)
        except: raise
        for t in img_download_threads: t.start()
        results[channel_title] = channel_vids
    keys = list(results)
    random.shuffle(keys)
    for key in keys: results.move_to_end(key)
    return results

def download_image(tf, url):
    tf.write(pool_manager.request('GET', url, preload_content=False).read())
    tf.close()

def html_decode(s):
    """
    Returns the ASCII decoded version of the given HTML string. This does
    NOT remove normal HTML tags like <p>.
    """
    html_codes = (
            ("'", '&#39;'),
            ('"', '&quot;'),
            ('>', '&gt;'),
            ('<', '&lt;'),
            ('&', '&amp;')
        )
    for html_code in html_codes:
        s = s.replace(html_code[1], html_code[0])
    return s

def get_front_page(ccount, vcount):
    service = get_authenticated_service()
    subs_dict = service.subscriptions().list(part='id,snippet', maxResults=ccount, mine=True).execute()
    subs = subs_dict['items']
    front_page = OrderedDict()
    for sub_ix,i in enumerate(subs):
        channel_snippet = i['snippet']
        channel_id = channel_snippet['resourceId']['channelId'] 
        channel_title = html_decode(channel_snippet['title'])
        response = service.search().list(part='snippet', maxResults=vcount, channelId=channel_id, order='date', type='').execute()
        channel_vids = []
        img_download_threads = []
        for vid_ix,cv in enumerate(response['items']):
            try:
                if 'videoId' in cv['id']:
                    vid_snippet = cv['snippet']
                    vid = {}
                    vid['id'] = cv['id']['videoId']
                    vid['lnk'] = 'https://youtube.com/watch?v=' + vid['id']
                    vid['ttl'] = html_decode(vid_snippet['title'])
                    vid['dsc'] = html_decode(vid_snippet['description'])
                    vid['dat'] = datetime.datetime.strptime(vid_snippet['publishedAt'].replace('.000Z', ''), '%Y-%m-%dT%H:%M:%S')
                    vid['stats'] = get_authenticated_service().videos().list(part='statistics', id=vid['id']) #.execute()['items'][0]['statistics']
                    tf = tempfile.NamedTemporaryFile(delete=False)
                    vid['tf'] = tf.name
                    channel_vids.append(vid)
                    img_url = vid_snippet['thumbnails']['high']['url']
                    img_download_threads.append(threading.Thread(target=download_image, args=[tf,img_url]))
            except: raise
        for t in img_download_threads: t.start()
        front_page[channel_title] = channel_vids
    keys = list(front_page)
    random.shuffle(keys)
    for key in keys: front_page.move_to_end(key)
    return front_page

def get_home_page():
    service = get_authenticated_service()
    log.debug('Authenticated')
    subs_dict = service.activities().list(part='snippet', maxResults=25, home=True,).execute()
    return subs_dict

if __name__ == '__main__':
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    results = get_front_page(1,1)
    # results = search('kek', 10, part='snippet')
    code.interact(local=globals().update(locals()) or globals())
