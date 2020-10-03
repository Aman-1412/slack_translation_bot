from pathlib import Path
import speech_recognition as sr
from os import path
from pydub import AudioSegment

from app_logger import logger


def speech_to_text(input_audio, input_audio_language):
    # files  output/audio_files/
    output_file = "test_wav.wav"
    sound = AudioSegment.from_mp3(input_audio)
    sound.export(output_file, format="wav")

    r = sr.Recognizer()

    with sr.AudioFile(output_file) as source:
        audio = r.record(source)
        logger.info('Audio found...')

    try:
        text = r.recognize_google(audio, language=input_audio_language)
        logger.info('working on...')
        # logger.info(text)
    except:
        text = 'Sorry, could not recognize your voice'
    finally:
        logger.info(f"Transcribed text in source language is: {text}")
        try:
            Path(output_file).unlink()
        except FileNotFoundError:
            pass
        return text
