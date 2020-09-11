#!/usr/bin/env python3

import os
import time
import logging

from pathlib import Path


from flask import Flask
from slack import WebClient
from slack.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


LOG_FILE = f'{Path(__file__).absolute().parent.parent}/logs/{Path(__file__).name}-file-{time.time()}.log'
print(LOG_FILE)
# Create a .env file containing the following details
SLACK_CLIENT_ID=os.environ['SLACK_CLIENT_ID']
SLACK_CLIENT_SECRET=os.environ['SLACK_CLIENT_SECRET']
SLACK_SIGNING_SECRET=os.environ['SLACK_SIGNING_SECRET']
SLACK_BOT_ACCESS_TOKEN=os.environ['SLACK_BOT_ACCESS_TOKEN']


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
file_handler = logging.FileHandler(LOG_FILE) 
file_handler.setFormatter(file_formatter) 

stream_formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s') 
stream_handler = logging.StreamHandler() 
stream_handler.setFormatter(stream_formatter) 

logger.addHandler(file_handler) 
logger.addHandler(stream_handler)


logger.info("Vars loaded and loggers in place")

# Initialize a Flask app to host the events adapter
app = Flask(__name__)
# Create an events adapter and register it to an endpoint in the slack app for event injestion.
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=SLACK_BOT_ACCESS_TOKEN)


# When a 'message' event is detected by the events adapter, forward that payload
# to this function.
@slack_events_adapter.on("message")
def message(payload):
    """Parse the message event, and echo it back
    """
    logger.info("Some message was posted in the channel")

     # Get the event data from the payload
    event = payload.get("event", {})

    # Get the text from the event that came through
    text = event.get("text")
    if "has joined the channel" in text:
        return
    user_id = event.get("user")
    if user_id == "U019Y2Q1FUL":
        return
    channel_id = event.get("channel")

    logger.info("Data retrieved from the event")

    try:
        # slack_web_client.chat_postEphemeral()
        slack_web_client.chat_postMessage(
            channel=channel_id,
            text=f"{text} said by {user_id}"
        )
    except SlackApiError:
        logger.error("Failed to send message", exc_info=True)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
