import os
import requests
from flask import Flask, request
​
API_KEY = ""
​
app = Flask(__name__)
@app.route('/translate', methods=['GET'])
def translate():
   # parse args
   TEXT=request.args.get('text')
   target=request.args.get('target')
   TRANSLATE_BASE_URL = f"https://translation.googleapis.com/language/translate/v2?target={target}&key={API_KEY}&q={TEXT}"
   # make the request
   r = requests.get(TRANSLATE_BASE_URL)
   response = r.json()['data']['translations'][0]['translatedText']
   return response
​
​
if __name__ == '__main__':
   app.run(debug=True)