import urllib
import urllib.request
import json
import os

# Get the title of youtube video with link


def getTitle(url: str) -> str:
    params = {"format": "json", "url": url}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return data['title']
# Create a csv file if not exists


def create(channel_id) -> None:
    if not os.path.exists(f'{channel_id}.csv'):
        open(f'{channel_id}.csv', 'w+').close()
