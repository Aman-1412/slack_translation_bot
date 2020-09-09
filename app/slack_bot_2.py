import os
import time
import json
import logging

from pathlib import Path


from flask import Flask , jsonify
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


LOG_FILE = f'{Path(__file__).absolute().parent.parent}/logs/{Path(__file__).name}-file-{time.time()}.log'
print(LOG_FILE)
# Create a .env file containing the following details




# Initialize a Flask app to host the events adapter
app = Flask(__name__)
# Create an events adapter and register it to an endpoint in the slack app for event injestion.
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=SLACK_BOT_ACCESS_TOKEN)

#when the app starts, load the language_mappings.json file and create a json for /change_language command. Any changes to language list to just be done
#in language_mappings.json file
with open('language_mapping.json') as language:
    language_mappings = json.load(language)
# print("Type:", type(language_mappings))
jsonres = {
    "text": "Please choose your preferred language",
    "response_type": "in_channel",
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
    jsonres["attachments"][0]["actions"][0]["options"].append({"text":key, "value":language_mappings[key]})


#endpoint for /change_language
@app.route('/slack/event/change_language', methods=['POST'])
def changelang():
    print("In change lang funcv")
    return jsonify(jsonres)

@slack_events_adapter.on("message")
def message(payload):
    """Parse the message event, and echo it back
    """
    print("Some message was posted in the channel")

     # Get the event data from the payload
    event = payload.get("event", {})

    text = event.get("text")
    user_id = event.get("user")
    if user_id == "U019Y2Q1FUL" or text=='Would you like to play a game':
        return
    channel_id = event.get("channel")

    
    if event.get("subtype") == 'channel_join':
        print(event.get("subtype"))
        try:
        # slack_web_client.chat_postEphemeral()
            response = slack_web_client.chat_postMessage(
            attachments=jsonres["attachments"],
            channel=channel_id,
            text="Hello Buddy"
            )
            return
        except SlackApiError as e:
            print("Failed to send message", exc_info=True)


    # Get the text from the event that came through
    

    print("Data retrieved from the event")

    try:
        # slack_web_client.chat_postEphemeral()
        response = slack_web_client.chat_postMessage(
            channel=channel_id,
            text=f"{text} said by {user_id}"
        )
    except SlackApiError as e:
        print("Failed to send message", exc_info=True)


@slack_events_adapter.on("interactive_message")
def onLanguageSelection(payload):

    #payload = '{"type":"interactive_message","actions":[{"name":"games_list","type":"select","selected_options":[{"value":"poker"}]}],"callback_id":"game_selection","team":{"id":"T01ADRFU9CY","domain":"agileexpress"},"channel":{"id":"C01A2KLGEJV","name":"bot_test"},"user":{"id":"U019WMG2EUU","name":"imrohitsaroha"},"action_ts":"1599500701.464930","message_ts":"1599500661.002300","attachment_id":"1","token":"JWMszEqPfb5j2XONBsbHqQZ2","is_app_unfurl":false,"original_message":{"type":"message","subtype":"bot_message","text":"Would you like to play a game?","ts":"1599500661.002300","bot_id":"B019NQ3G18D","attachments":[{"callback_id":"game_selection","fallback":"If you could read this message, you'd be choosing something fun to do right now.","text":"Choose a game to play","id":1,"color":"3AA3E3","actions":[{"id":"1","name":"games_list","text":"Pick a game...","type":"select","data_source":"static","options":[{"text":"Hearts","value":"hearts"},{"text":"Bridge","value":"bridge"},{"text":"Checkers","value":"checkers"},{"text":"Chess","value":"chess"},{"text":"Poker","value":"poker"},{"text":"Falken's Maze","value":"maze"},{"text":"Global Thermonuclear War","value":"war"}]}]}]},"response_url":"https:\/\/hooks.slack.com\/actions\/T01ADRFU9CY\/1344860121109\/9Wq5lalGC9H0Q9shuhbABUoi","trigger_id":"1333202800375.1353865961440.f2683796eda1b08b34f324b0efdbcc98"}'

    print("In interactive_message")
    print("Type of Payload" + type(payload))
    payload = json.loads(payload)
    print(payload)

    event = payload.get("event", {})
    variable = payload.get("actions")
    print(variable)
    # Get the id of the Slack user associated with the incoming event
    user_id = event.get("user", {}).get("id")
    if user_id == "U019Y2Q1FUL":
        return

    # Open a DM with the new user.
    try:
        # slack_web_client.chat_postEphemeral()
        response = slack_web_client.chat_postEphemeral(
            user = user_id,
            channel=channel_id,
            text = user_id + " " + " selected value " + "variable"
        )
    except SlackApiError as e:
        print("Failed to send message", exc_info=True)
    

@slack_events_adapter.on("team_join")
def teamJoined(payload):
    """Create and send an onboarding welcome message to new users. Save the
    time stamp of this message so we can update this message in the future.
    """

    print("In member_jteam_joinoined_channel method")
    event = payload.get("event", {})

    (getActualEvent(event))

    # Get the id of the Slack user associated with the incoming event
    user_id = event.get("user", {}).get("id")
    if user_id == "U019Y2Q1FUL":
        return

    # Open a DM with the new user.
    try:
        # slack_web_client.chat_postEphemeral()
        response = slack_web_client.chat_postEphemeral(
            user = user_id,
            channel=channel_id,
            text="Hello Buddy"
        )
    except SlackApiError as e:
        print("Failed to send message", exc_info=True)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)