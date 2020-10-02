
import speech_recognition as sr
from os import path
from pydub import AudioSegment

def speech_to_text(input_audio,input_audio_language):
  # files  output/audio_files/                                                                       
  dst = "test_wav.wav"
                                                              
  sound = AudioSegment.from_mp3(input_audio)
  sound.export(dst, format="wav")

  r = sr.Recognizer()

  with sr.AudioFile(dst) as source:
    audio = r.record(source)
    print('Audio found...')
    
  try:
      print('convert now...')
      text = r.recognize_google(audio, language=input_audio_language)
      print('working on...')
      #print(text)
      return text
  except :
      print('sorry could not recognize your voice')
      return None


 