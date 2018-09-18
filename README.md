# fb-page-chat-download
Python script to download message history from a Facebook page you manage to a CSV file. It uses the latest Graph API version available at the time of writing which is v2.6. I hacked this together in a few hours, contributions are always appreciated.

How to use:
 * Go to https://developers.facebook.com/tools/explorer and click 'Get User Access Token'
 * Make sure to check 'manage_pages' and 'read_page_mailboxes'
 * Switch to a page that you want to scrape
 * Get the page_id and the access token to pass as parameters to this script

This token will expire in an hour, alternatively you can create or use your app and grant the app those same permitions.

Dependencies: A python 3 env
```
pip install unidecode
pip install requests
```
Or alternatively do `pipenv install` if you are using [pipenv](https://pipenv.readthedocs.io/en/latest/)

Then run it using:
```
python fb-page-chat-download/run.py <PAGE_ID> <OUTPUT_FILE> <ACCESS_TOKEN>
```
    
Optional parameters to filter by time are added. Currently by default the last 500 conversations threads are scraped entirely.
