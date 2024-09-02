import os
import json
import requests
from requests_oauthlib import OAuth1Session

consumer_key = '####'
consumer_secret = '########'

def get_random_word():
    response = requests.get("https://random-word-api.herokuapp.com/word?lang=en")
    if response.status_code == 200:
        return response.json()[0]
    return None

def get_definition_and_example(word):
    response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    if response.status_code == 200:
        data = response.json()[0]
        meanings = data.get('meanings', [])
        if meanings:
            definition = meanings[0]['definitions'][0]['definition']
            example = meanings[0]['definitions'][0].get('example')
            if example:
                return definition, example
    return None, None

def fetch_valid_word():
    while True:
        word = get_random_word()
        if word:
            definition, example = get_definition_and_example(word)
            if definition and example:
                return word, definition, example

def split_message(message, max_length=280):
    # Split message into chunks of max_length
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

def post_tweet(text, reply_to=None):
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text}
    if reply_to:
        payload['reply'] = {"in_reply_to_tweet_id": reply_to}
    response = oauth.post(url, json=payload)
    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(response.status_code, response.text)
        )
    return response.json()

# Main logic
word, definition, example = fetch_valid_word()
text_message = f"Word: {word}\n\nDefinition: {definition}\n\nExample: {example}"

# Split the long text_message into smaller tweets if needed
tweets = split_message(text_message)

# Check if we already have access tokens saved
tokens_file = 'twitter_tokens.json'
if os.path.exists(tokens_file):
    with open(tokens_file, 'r') as file:
        tokens = json.load(file)
    access_token = tokens['access_token']
    access_token_secret = tokens['access_token_secret']
else:
    # Get request token
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print("There may have been an issue with the consumer_key or consumer_secret you entered.")
        exit()

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    print("Got OAuth token: %s" % resource_owner_key)

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    # Save the obtained tokens to a file for future use
    with open('twitter_tokens.json', 'w') as file:
        json.dump({
            'access_token': access_token,
            'access_token_secret': access_token_secret
        }, file)

# Make the request
oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

# Post the first tweet
first_tweet = post_tweet(tweets[0])
last_tweet_id = first_tweet['data']['id']

# Post the rest of the tweets as replies to the previous tweet
for tweet_text in tweets[1:]:
    response = post_tweet(tweet_text, reply_to=last_tweet_id)
    last_tweet_id = response['data']['id']
