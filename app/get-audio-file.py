import requests
from datetime import datetime
import speech

def get_audio_file(url, user_id):
    r = requests.get(url,
    headers={
        'Authorization': 'Bearer %s' %TOKEN
        })
    #file_name = 'input/audio_files/' + user_id + (datetime.utcnow().strftime('%Y-%m-%d-%H_%M_%S')) + '.mp3'
    file_name = 'input/audio_files/-10-02-10_55_25.mp3'
    file_data= r.content
    with open(file_name, 'w+b') as f:
        f.write(bytearray(file_data))
        print("Saved " + file_name)
    return file_name


#name = get_audio_file('https://files.slack.com/files-pri/T01ADRFU9CY-F01BV0EGN1Z/download/recordfy__2_.mp3', "rohit")