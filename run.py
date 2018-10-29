#!/usr/bin/env python
# encoding: utf-8

"""
How to use:
 * Go to https://developers.facebook.com/tools/explorer and click 'Get User Access Token'
 * Then select 'manage_pages' and 'read_page_mailboxes'
 * Switch to a page that you want to scrape
 * Get the page_id and the token and pass as parameters to this script
"""

import os
import csv
import json
import requests
import argparse
import sys
import re
import datetime
import unidecode
import concurrent.futures

CONNECTIONS = 100

class FBScraper:
    def __init__(self, page, output, token, since=None, until=None):
        self.token = token
        self.output = output
        self.since = since
        self.until = until
        self.uri = self.build_url('{}/conversations?fields=participants,link&limit=400', page)

    def build_url(self, endpoint, *params):
        buildres = "https://graph.facebook.com/v3.1/" + endpoint.format(*params) + '&access_token={}'.format(self.token)
        print("URL: ", buildres)
        return buildres

    def scrape_thread(self, url, lst):
        if self.since:
            matches = re.findall('&until=(\d+)', url)
            if matches and int(matches[0]) <= self.since:
                return lst

        messages = requests.get(url).json()
        for m in messages['data']:
            time = datetime.datetime.strptime(m['created_time'], '%Y-%m-%dT%H:%M:%S+0000').replace(tzinfo=datetime.timezone.utc).timestamp()
            if self.since and time < self.since:
                continue
            if self.until and time > self.until:
                continue
            lst.append({
                'time': m['created_time'].replace('+0000', '').replace('T', ' '),
                'message': m['message'],
                'attachments': m.get('attachments', {}).get('data', [{}])[0].get('image_data', {}).get('url', ''),
                'shares': m.get('shares', {}).get('data', [{}])[0].get('name', ''),
                'from_id': m['from']['id']
            })
        # if messages['data']:
        #     print(' +', len(messages['data']))
        next = messages.get('paging', {}).get('next', '')
        if next:
            self.scrape_thread(next, lst)
        return lst

    def get_messages(self, t):
        extra_params = (('&since=' + str(self.since)) if self.since else '') + (('&until=' + str(self.until)) if self.until else '')
        url = self.build_url('{}/messages?fields=from,created_time,message,shares,attachments&limit=400' + extra_params, t['id'])
        thread = self.scrape_thread(url, [])
        if thread:
            print(
                thread[0]['time'], 
                t['id'].ljust(20), 
                str(len(thread)).rjust(3) + ' from', 
                unidecode.unidecode(t['participants']['data'][0]['name'])
            )
            id_map = {p['id']: p['name'] for p in t['participants']['data']}
            for message in thread:
                message['from'] = id_map[message['from_id']]

            return [{
                # 'page_id': t['participants']['data'][1]['id'],
                # 'page_name': t['participants']['data'][1]['name'],
                # 'user_id': t['participants']['data'][0]['id'],
                # 'user_name': t['participants']['data'][0]['name'],
                'url': t['link'],
            }] + list(reversed(thread))
        return []
        
    def scrape_thread_list(self, threads, count):
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
            futures = (executor.submit(self.get_messages, conv) for conv in threads['data'])
            for future in concurrent.futures.as_completed(futures):
                messages = future.result()
                for message in messages:
                    self.writer.writerow(message)
        next = threads.get('paging', {}).get('next', '')
        if next and count > 1:
            self.scrape_thread_list(requests.get(next).json(), count - 1)
        

    def run(self):
        output = open(self.output, 'w', newline="\n", encoding="utf-8")
        threads = requests.get(self.uri).json()
        if 'error' in threads:
            print(threads)
            return

        fieldnames = ['from_id', 'from', 'time', 'message', 'attachments', 'shares', 'url']
        self.writer = csv.DictWriter(output, dialect='excel', fieldnames=fieldnames, extrasaction='ignore', quoting=csv.QUOTE_NONNUMERIC)
        self.writer.writerow(dict((n, n) for n in fieldnames))
        self.scrape_thread_list(threads, 20)
        output.close()

def main():
    """
        Main method
    """
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('page', metavar='page_id', type=int, nargs=1, help='Facebook Page ID')
    parser.add_argument('output', metavar='output_file', type=str, nargs=1, help='CSV Output File')
    parser.add_argument('token', metavar='access_token', type=str, nargs=1, help='Access Token')
    parser.add_argument('--since', metavar='since_epoch', type=int, nargs='?', help='Filter messages from after this time')
    parser.add_argument('--until', metavar='until_epoch', type=int, nargs='?', help='Filter messages from before this time')
    args = parser.parse_args()

    print("pageid: ", args.page[0])
    print("csv: ", args.output[0])
    print("token: ", args.token[0])
    print("since: ", args.since)
    print("until: ", args.until)
    
    FBScraper(args.page[0], args.output[0], args.token[0], args.since, args.until).run()

if __name__ == "__main__":
    main()
