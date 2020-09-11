import app_logger
import translate_api
#import redis_utils
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


LOG_FILE = f'{Path(__file__).absolute().parent.parent}/logs/{Path(__file__).name}-file-{time.time()}.log'
logging.info(LOG_FILE)
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
    logging.info("First run?")

# when the app starts, load the language_mappings.json file and create a json for /change_language command. Any changes to language list to just be done
# in language_mappings.json file
with open(f'{Path(__file__).parent}/language_mapping.json') as language:
    language_mappings = json.load(language)
# logging.info("Type:", type(language_mappings))
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
for(key) in language_mappings:
    language_selecter["attachments"][0]["actions"][0]["options"].append(
        {"text": key, "value": language_mappings[key]})


def get_name_from_user_id(user_id):
    logging.info(f'Getting user name for {user_id}')
    URL = f'https://slack.com/api/users.info?token={SLACK_BOT_ACCESS_TOKEN}&user={user_id}'
    response_json = requests.get(URL).json()
    logging.info(f'Request json is {response_json}')
    return response_json['user']['profile']['real_name_normalized'].title()



def get_language_from_iso_code(iso_code):
    for k, v in language_mappings.items():
        if v == iso_code:
            return k


def get_translated_message(text, source_language, target_language):
    if source_language == target_language:
        return text
    # translated_text = redis_utils.get_translated_text(
    #     text, source_language, target_language)
    translated_text=None
    if translated_text is None:
        translated_text = translate_api.translate(
            GOOGLE_TRANSLATE_API_KEY, text, source_language, target_language)
        translated_text = html.unescape(translated_text)
        # redis_utils.set_translated_text(
        #     text, source_language, target_language, translated_text)
    return translated_text


# endpoint for /change_language
@app.route('/slack/event/change_language', methods=['POST'])
def choose_language():
    logging.info("In change lang funcv")
    return jsonify(language_selecter)


@app.route('/slack/event/valueSelected', methods=['POST'])
def set_language():
    global USER_LANGUAGE_MAPPINGS
    payload = request.form.get('payload')
    logging.info("Type of Payload " + str(type(payload)))
    payload = json.loads(payload)
    logging.info(payload)
    channel_id = payload.get('channel').get('id')
    logging.info('channel_id ' + channel_id)
    selected_language_iso_code = payload.get(
        'actions')[0].get('selected_options')[0].get('value')
    logging.info("Selected Value is " + selected_language_iso_code)
    userId = payload.get('user').get('id')
    logging.info('userId ' + userId)
    user_name = get_name_from_user_id(userId)
    if not channel_id in USER_LANGUAGE_MAPPINGS:
        USER_LANGUAGE_MAPPINGS[channel_id] = {}
    USER_LANGUAGE_MAPPINGS[channel_id].update(
        {userId: selected_language_iso_code})
    with open(f'{Path(__file__).parent}/user_language_mapping.json', 'w') as fp:
        json.dump(USER_LANGUAGE_MAPPINGS, fp, sort_keys=True, indent=4)

    selected_language_text = get_language_from_iso_code(
        selected_language_iso_code)
    selection_success = {
        "text": f"Thank You {user_name}. Your language has been set to {selected_language_text}. Please use /change_language to change it again."
    }

    return jsonify(selection_success)

def process_message(event, user_id, channel_id, text):
    global USER_LANGUAGE_MAPPINGS
    user_name = get_name_from_user_id(user_id)
    # source_language = USER_LANGUAGE_MAPPINGS[channel_id].get(user_id, None)
    # TODO: update this condition when using the new bot
    if user_id == "U01AUR3FS2V" or text == 'Please choose your preferred language':
        return
    
    text = text.replace("'", "\\'")

    # When a new user joins
    if event.get("subtype") == 'channel_join':
        logging.info(event.get("subtype"))
        if not channel_id in USER_LANGUAGE_MAPPINGS:
            USER_LANGUAGE_MAPPINGS[channel_id] = {}
        USER_LANGUAGE_MAPPINGS[channel_id].update({user_id: 'en'})
        with open(f'{Path(__file__).parent}/user_language_mapping.json', 'w') as fp:
            json.dump(USER_LANGUAGE_MAPPINGS, fp, sort_keys=True, indent=4)
        try:
            # slack_web_client.chat_postEphemeral() #chat_postMessage
            slack_web_client.chat_postEphemeral(
                user=user_id,
                attachments=language_selecter["attachments"],
                channel=channel_id,
                text=f"Hello {user_name}")
            return
        except SlackApiError:
            logging.info("Failed to send message", exc_info=True)
    # ENDS HERE
    source_language = translate_api.detect_language(GOOGLE_TRANSLATE_API_KEY, text)

    # When a message is posted, translate it for all the users in the channel
    for target_user_id, target_language in USER_LANGUAGE_MAPPINGS.get(channel_id).items():
        logging.info(f'Target user_id is {target_user_id} and target language is {target_user_id} ')
        if target_user_id != user_id: 
            translated_text = get_translated_message(
                text, source_language, target_language)
            logger.info(f'*************************translated text is {translated_text}')
            try:
                # slack_web_client.chat_postEphemeral()
                slack_web_client.chat_postEphemeral(
                    user=target_user_id,
                    channel=channel_id, 
                    text=f"*{user_name}* :\n{translated_text} "
                )
            except SlackApiError:
                logging.info("Failed to send message", exc_info=True)


@slack_events_adapter.on("message")
def message(payload):
    global USER_LANGUAGE_MAPPINGS
    logging.info("Some message was posted in the channel")

    # Get the event data from the payload
    event = payload.get("event", {})
    channel_id = event.get("channel")
    text = event.get("text")
    user_id = event.get("user")
    x = threading.Thread(target=process_message, args=(event, user_id, channel_id,text), daemon=True)
    x.start()
    return

    
    # try:
    #     # slack_web_client.chat_postEphemeral()
    #     response = slack_web_client.chat_postMessage(
    #         channel=channel_id,
    #         text=f"{text} said by {user_id}"
    #     )
    # except SlackApiError as e:
    #     logging.info("Failed to send message", exc_info=True)


# @slack_events_adapter.on("interactive_message")
# def onLanguageSelection(payload):

#     #payload = '{"type":"interactive_message","actions":[{"name":"games_list","type":"select","selected_options":[{"value":"poker"}]}],"callback_id":"game_selection","team":{"id":"T01ADRFU9CY","domain":"agileexpress"},"channel":{"id":"C01A2KLGEJV","name":"bot_test"},"user":{"id":"U019WMG2EUU","name":"imrohitsaroha"},"action_ts":"1599500701.464930","message_ts":"1599500661.002300","attachment_id":"1","token":"JWMszEqPfb5j2XONBsbHqQZ2","is_app_unfurl":false,"original_message":{"type":"message","subtype":"bot_message","text":"Would you like to play a game?","ts":"1599500661.002300","bot_id":"B019NQ3G18D","attachments":[{"callback_id":"game_selection","fallback":"If you could read this message, you'd be choosing something fun to do right now.","text":"Choose a game to play","id":1,"color":"3AA3E3","actions":[{"id":"1","name":"games_list","text":"Pick a game...","type":"select","data_source":"static","options":[{"text":"Hearts","value":"hearts"},{"text":"Bridge","value":"bridge"},{"text":"Checkers","value":"checkers"},{"text":"Chess","value":"chess"},{"text":"Poker","value":"poker"},{"text":"Falken's Maze","value":"maze"},{"text":"Global Thermonuclear War","value":"war"}]}]}]},"response_url":"https:\/\/hooks.slack.com\/actions\/T01ADRFU9CY\/1344860121109\/9Wq5lalGC9H0Q9shuhbABUoi","trigger_id":"1333202800375.1353865961440.f2683796eda1b08b34f324b0efdbcc98"}'

#     logging.info("In interactive_message")
#     logging.info("Type of Payload" + type(payload))
#     payload = json.loads(payload)
#     logging.info(payload)

#     event = payload.get("event", {})
#     variable = payload.get("actions")
#     logging.info(variable)
#     # Get the id of the Slack user associated with the incoming event
#     user_id = event.get("user", {}).get("id")
#     # TODO: replace this with the current bot id
#     if user_id == "U019Y2Q1FUL":
#         return

#     # Open a DM with the new user.
#     try:
#         # slack_web_client.chat_postEphemeral()
#         response = slack_web_client.chat_postEphemeral(
#             user = user_id,
#             channel=channel_id,
#             text = user_id + " " + " selected value " + "variable"
#         )
#     except SlackApiError as e:
#         logging.info("Failed to send message", exc_info=True)


# @slack_events_adapter.on("team_join")
# def teamJoined(payload):
#     """Create and send an onboarding welcome message to new users. Save the
#     time stamp of this message so we can update this message in the future.
#     """

#     logging.info("In member_jteam_joinoined_channel method")
#     event = payload.get("event", {})

#     (getActualEvent(event))

#     # Get the id of the Slack user associated with the incoming event
#     user_id = event.get("user", {}).get("id")
#     if user_id == "U019Y2Q1FUL":
#         return

#     # Open a DM with the new user.
#     try:
#         # slack_web_client.chat_postEphemeral()
#         response = slack_web_client.chat_postEphemeral(
#             user = user_id,
#             channel=channel_id,
#             text="Hello Buddy"
#         )
#     except SlackApiError as e:
#         logging.info("Failed to send message", exc_info=True)


if __name__ == "__main__":
    # TODO: remove debug
    app.run(host='0.0.0.0', port=3000, debug=True)
