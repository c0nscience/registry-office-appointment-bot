from bs4 import BeautifulSoup
import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
}


def hello(event, context):
    params = {
        'termin': 1,
        'dienstleisterlist': '122210',
        'anliegen': '120335',
    }
    response = requests.get('https://service.berlin.de/terminvereinbarung/termin/tag.php', params=params,
                            headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    body = {
        "title": soup.title.string
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
