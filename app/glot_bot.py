
import os
import time
import json
import logging
import html
import threading

from pathlib import Path

import requests
from flask import Flask, jsonify, request
from slack import WebClient
from slack.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import app_logger
import redis_utils
import translate_api


LOG_FILE = f'{Path(__file__).absolute().parent.parent}/logs/{Path(__file__).name}-file-{time.time()}.log'

# Create a .env file containing the following details
SLACK_CLIENT_ID = os.environ['SLACK_CLIENT_ID']
SLACK_CLIENT_SECRET = os.environ['SLACK_CLIENT_SECRET']
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
SLACK_BOT_ACCESS_TOKEN = os.environ['SLACK_BOT_ACCESS_TOKEN']
GOOGLE_TRANSLATE_API_KEY = os.environ['GOOGLE_TRANSLATION_API_KEY']


logger = app_logger.get_logger(LOG_FILE)
logger.info("Vars loaded and loggers in place")

# Initialize a Flask app to host the events adapter
app = Flask(__name__)
# Create an events adapter and register it to an endpoint in the slack app for event injestion.
slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=SLACK_BOT_ACCESS_TOKEN)

try:
    with open(f'{Path(__file__).parent}/user_language_mapping.json') as f:
        USER_LANGUAGE_MAPPINGS = json.load(f)
except FileNotFoundError:
    USER_LANGUAGE_MAPPINGS = {}
    logger.info("First run?")

# when the app starts, load the language_mappings.json file and create a json for /change_language command. Any changes to language list to just be done
# in language_mappings.json file
with open(f'{Path(__file__).parent}/language_mapping.json') as language:
    LANGUAGE_ISO_MAPPING = json.load(language)

language_selecter = {
    "text": "Please choose your preferred language",
    "response_type": "ephemeral",
    "attachments": [
        {
            "text": "Select a language",
            "fallback": "If you could read this message, ",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "callback_id": "language_selection",
            "actions": [
                {
                    "name": "language_list",
                    "text": "Select a language...",
                    "type": "select",
                    "options": []
                }
            ]
        }
    ]
}
for(key) in LANGUAGE_ISO_MAPPING:
    language_selecter["attachments"][0]["actions"][0]["options"].append(
        {"text": key, "value": LANGUAGE_ISO_MAPPING[key]})


def get_name_from_user_id(user_id):
    URL = f'https://slack.com/api/users.info?token={SLACK_BOT_ACCESS_TOKEN}&user={user_id}'
    response_json = requests.get(URL).json()
    try:
        name = response_json['user']['profile']['real_name_normalized'].title()
        logger.debug("Name fetched successfully")
        return name
    except:
        logger.error(
            f"Some error getting the name, response is {response_json}")
        return user_id


def get_language_from_iso_code(iso_code):
    for k, v in LANGUAGE_ISO_MAPPING.items():
        if v == iso_code:
            return k


def get_translated_message(text, source_language, target_language):
    if source_language == target_language:
        return text
    translated_text = redis_utils.get_translated_text(
        text, source_language, target_language)
    if translated_text is None:
        translated_text = translate_api.translate(
            GOOGLE_TRANSLATE_API_KEY, text, source_language, target_language)
        translated_text = html.unescape(translated_text)
        redis_utils.set_translated_text(
            text, source_language, target_language, translated_text)
    return translated_text


@app.route('/slack/event/change_language', methods=['POST'])
def choose_language():
    logger.debug("Sending the attachment to let user choose their language")
    return jsonify(language_selecter)


@app.route('/slack/event/valueSelected', methods=['POST'])
def set_language():
    global USER_LANGUAGE_MAPPINGS

    payload = json.loads(request.form.get('payload'))
    channel_id = payload.get('channel').get('id')
    selected_language_iso_code = payload.get(
        'actions')[0].get('selected_options')[0].get('value')
    user_id = payload.get('user').get('id')
    user_name = get_name_from_user_id(user_id)
    selected_language_text = get_language_from_iso_code(
        selected_language_iso_code)

    if not channel_id in USER_LANGUAGE_MAPPINGS:
        USER_LANGUAGE_MAPPINGS[channel_id] = {}
    USER_LANGUAGE_MAPPINGS[channel_id].update(
        {user_id: selected_language_iso_code})
    with open(f'{Path(__file__).parent}/user_language_mapping.json', 'w') as fp:
        json.dump(USER_LANGUAGE_MAPPINGS, fp, sort_keys=True, indent=4)

    logger.info(
        f"{user_name}'s language changed to {selected_language_text} in channel {channel_id}")

    selection_success = {
        "text": f"Thank You *{user_name}.* Your language has been set to *{selected_language_text}.* Please use */change_language* to change it again."
    }

    return jsonify(selection_success)


def process_message(event, user_id, channel_id, text):
    global USER_LANGUAGE_MAPPINGS
    user_name = get_name_from_user_id(user_id)
    logger.info(f"Sender of the message is {user_name}")

    # When a new user joins
    if event.get("subtype") == 'channel_join':
        logger.info(event.get("subtype"))
        if not channel_id in USER_LANGUAGE_MAPPINGS:
            USER_LANGUAGE_MAPPINGS[channel_id] = {}
        USER_LANGUAGE_MAPPINGS[channel_id].update({user_id: 'en'})
        with open(f'{Path(__file__).parent}/user_language_mapping.json', 'w') as fp:
            json.dump(USER_LANGUAGE_MAPPINGS, fp, sort_keys=True, indent=4)
        try:
            slack_web_client.chat_postEphemeral(
                user=user_id,
                attachments=language_selecter["attachments"],
                channel=channel_id,
                text=f"Hello {user_name}")
            return
        except SlackApiError:
            logger.info("Failed to send message", exc_info=True)
    # ENDS HERE

    if text:
        text = text.replace("'", "\\'")
    source_language = translate_api.detect_language(
        GOOGLE_TRANSLATE_API_KEY, text)
    logger.info(
        f"Detected language of the message is {get_language_from_iso_code(source_language)}")

    # When a message is posted, translate it for all the users in the channel
    for target_user_id, target_language in USER_LANGUAGE_MAPPINGS.get(channel_id).items():
        if target_user_id != user_id:
            logger.info(
            f'Target user_id is {target_user_id} and target language is {get_language_from_iso_code(target_language)} ')
            start = time.time()
            translated_text = get_translated_message(
                text, source_language, target_language)
            logger.info(
                f'Translated text in {get_language_from_iso_code(target_language)} is {translated_text}. Completed in {time.time()-start} seconds')
            try:
                slack_web_client.chat_postEphemeral(
                    user=target_user_id,
                    channel=channel_id,
                    text=f"*{user_name}* :\n{translated_text} "
                )
            except SlackApiError:
                logger.error("Failed to send message", exc_info=True)


@slack_events_adapter.on("message")
def message(payload):
    global USER_LANGUAGE_MAPPINGS
    logger.debug("A message was posted in the channel")

    # Get the event data from the payload
    event = payload.get("event", {})
    # Handle edited messages
    if event.get("subtype",'') == 'message_changed':
        logger.debug("It is an edited message")
        # If the message was edited by bot. Return
        if event.get("message",{}).get("subtype",'') == 'bot_message':
            logger.debug("The message was edited by the bot! Doing nothing")
            return
        else:
            text = event.get("message",{}).get("text")
            user_id = event.get("message",{}).get("user")

    elif event.get("subtype",'') == 'bot_add':
        logger.debug("Bot was added to the channel")
        return
        
    elif 'files' in event:
        files = event.get("files")
        audio_url = files.get("url_private_download")
    
    else:
        text = event.get("text")
        user_id = event.get("user")

    channel_id = event.get("channel")
    if user_id == "U01AUR3FS2V" or text == 'Please choose your preferred language':
        logger.info("Beep Bop. I am a bot. Doing nothing")
        return
    x = threading.Thread(target=process_message, args=(
        event, user_id, channel_id, text), daemon=True)
    x.start()
    return


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
