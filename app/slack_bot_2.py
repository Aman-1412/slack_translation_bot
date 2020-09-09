import os
import time
import json
import logging

from pathlib import Path


from flask import Flask , jsonify, request
from slack import WebClient
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


# Initialize a Flask app to host the events adapter
app = Flask(__name__)
# Create an events adapter and register it to an endpoint in the slack app for event injestion.
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=SLACK_BOT_ACCESS_TOKEN)


#When a 'message' event is detected by the events adapter, forward that payload
#to this function.

attachmentMessage=[
        {
            "text": "Choose a game to play",
            "fallback": "If you could read this message, you'd be choosing something fun to do right now.",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "callback_id": "game_selection",
            "actions": [
                {
                    "name": "games_list",
                    "text": "Pick a game...",
                    "type": "select",
                    "options": [
                        {
                            "text": "Hearts",
                            "value": "hearts"
                        },
                        {
                            "text": "Bridge",
                            "value": "bridge"
                        },
                        {
                            "text": "Checkers",
                            "value": "checkers"
                        
                        },
                        {
                            "text": "Chess",
                            "value": "chess"
                        },
                        {
                            "text": "Poker",
                            "value": "poker"
                        },
                        {
                            "text": "Falken's Maze",
                            "value": "maze"
                        },
                        {
                            "text": "Global Thermonuclear War",
                            "value": "war"
                        }
                    ]
                }
            ]
        }
    ]

@app.route('/slack/event/change_language', methods=['POST'])
def changelang():
    print("In change lang funcv")
    jsonres = {
    "text": "Select your preffered language",
    "response_type": "in_channel",
    "attachments": [
        {
            "text": "Choose a game to play",
            "fallback": "If you could read this message, you'd be choosing something fun to do right now.",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "callback_id": "game_selection",
            "actions": [
                {
                    "name": "games_list",
                    "text": "Pick a game...",
                    "type": "select",
                    "options": [
                        {
                            "text": "Hearts",
                            "value": "hearts"
                        },
                        {
                            "text": "Bridge",
                            "value": "bridge"
                        },
                        {
                            "text": "Checkers",
                            "value": "checkers"
                        
                        },
                        {
                            "text": "Chess",
                            "value": "chess"
                        },
                        {
                            "text": "Poker",
                            "value": "poker"
                        },
                        {
                            "text": "Falken's Maze",
                            "value": "maze"
                        },
                        {
                            "text": "Global Thermonuclear War",
                            "value": "war"
                        }
                    ]
                }
            ]
        }
    ]
}


    return jsonify(jsonres)

@app.route('/slack/event/valueSelected', methods=['POST'])
def valueSelected():
    payload =  request.form.get('payload')
    print("Type of Payload " + str(type(payload)))
    payload = json.loads(payload)
    print(payload)
    jsonres = {
    "text": "Your Language has been set"
    }
    channelId = payload.get('channel').get('id')
    print('channelId ' + channelId)  
    selected_value=payload.get('actions')[0].get('selected_options')[0].get('value')
    print("Selected Value is " + str(type(selected_value)))
    userId = payload.get('user').get('id')
    print('userId ' + userId)

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
            attachments=attachmentMessage,
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




# @slack_events_adapter.on("interactive_message")
# def onLanguageSelection(payload):

#     #payload = '{"type":"interactive_message","actions":[{"name":"games_list","type":"select","selected_options":[{"value":"poker"}]}],"callback_id":"game_selection","team":{"id":"T01ADRFU9CY","domain":"agileexpress"},"channel":{"id":"C01A2KLGEJV","name":"bot_test"},"user":{"id":"U019WMG2EUU","name":"imrohitsaroha"},"action_ts":"1599500701.464930","message_ts":"1599500661.002300","attachment_id":"1","token":"JWMszEqPfb5j2XONBsbHqQZ2","is_app_unfurl":false,"original_message":{"type":"message","subtype":"bot_message","text":"Would you like to play a game?","ts":"1599500661.002300","bot_id":"B019NQ3G18D","attachments":[{"callback_id":"game_selection","fallback":"If you could read this message, you'd be choosing something fun to do right now.","text":"Choose a game to play","id":1,"color":"3AA3E3","actions":[{"id":"1","name":"games_list","text":"Pick a game...","type":"select","data_source":"static","options":[{"text":"Hearts","value":"hearts"},{"text":"Bridge","value":"bridge"},{"text":"Checkers","value":"checkers"},{"text":"Chess","value":"chess"},{"text":"Poker","value":"poker"},{"text":"Falken's Maze","value":"maze"},{"text":"Global Thermonuclear War","value":"war"}]}]}]},"response_url":"https:\/\/hooks.slack.com\/actions\/T01ADRFU9CY\/1344860121109\/9Wq5lalGC9H0Q9shuhbABUoi","trigger_id":"1333202800375.1353865961440.f2683796eda1b08b34f324b0efdbcc98"}'

#     print("In interactive_message")
#     print("Type of Payload " + str(type(payload)))
#     payload = json.loads(payload)
#     print(payload)

#     event = payload.get("event", {})
#     variable = payload.get("actions")
#     print(variable)
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
#             text = user_id + " " + " selected value " + "variable"
#         )
#     except SlackApiError as e:
#         print("Failed to send message", exc_info=True)
    

# @slack_events_adapter.on("team_join")
# def teamJoined(payload):
#     """Create and send an onboarding welcome message to new users. Save the
#     time stamp of this message so we can update this message in the future.
#     """

#     print("In member_jteam_joinoined_channel method")
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
#         print("Failed to send message", exc_info=True)
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)
