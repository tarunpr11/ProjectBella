import speech_recognition as sr
from gtts import gTTS
import os
import playsound
import sys

# A simple speak function
def speak(text):
    try:
        tts = gTTS(text=text, lang='en-IN', tld='co.in')
        audio_file = "question.mp3"
        tts.save(audio_file)
        playsound.playsound(audio_file)
        os.remove(audio_file)
    except Exception as e:
        print(f"Error in gTTS: {e}")

# A simple listen function
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your response...")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-IN')
        return query
    except Exception as e:
        print("Didn't catch that.")
        return ""

if __name__ == "__main__":
    # The first argument from UiPath will be the question to ask
    question_to_ask = sys.argv[1]
    
    speak(question_to_ask)
    response = listen()
    
    # Write the response to a file for UiPath to read
    with open("response.txt", "w") as f:
        f.write(response) 