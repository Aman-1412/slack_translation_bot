import os
import requests

from app_logger import logger

# def detect_language(source_text):
#       https://translation.googleapis.com/language/translate/v2/detect
#    {
#   "q": "Mi comida favorita es una enchilada."
# }
# {
#   "data": {
#     "detections": [
#       [
#         {
#           "confidence": 1,
#           "isReliable": false,
#           "language": "es"
#         }
#       ]
#     ]
#   }
# }


def detect_language(API_KEY, input_text):
    source_language = requests.get(
        f'https://translation.googleapis.com/language/translate/v2/detect?key={API_KEY}&q={input_text}').json()['data']['detections'][0][0]['language']
    return source_language


def translate(API_KEY, input_text, source_language, target_language):

    # if source_language:
    #    TRANSLATE_BASE_URL = f"https://translation.googleapis.com/language/translate/v2?source={source_language}&target={target_language}&key={API_KEY}&q={input_text}"
    # else:
    TRANSLATE_BASE_URL = f"https://translation.googleapis.com/language/translate/v2?source={source_language}&target={target_language}&key={API_KEY}&q={input_text}"
    try:
        r = requests.get(TRANSLATE_BASE_URL)
        translated_text = r.json()['data']['translations'][0]['translatedText']
    except:
        logger.error(f"Error while querying GCP API: {r.text}", exc_info=True)
    return translated_text
