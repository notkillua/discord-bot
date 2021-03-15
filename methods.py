import urllib
import urllib.request
import json
import os


def getTitle(url: str) -> str:
    params = {"format": "json", "url": url}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return data['title']


def create(channel_id) -> None:
    if not os.path.exists(f'{channel_id}.csv'):
        open(f'{channel_id}.csv', 'w+').close()
