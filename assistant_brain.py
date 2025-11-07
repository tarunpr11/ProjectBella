import speech_recognition as sr
import os
from dotenv import load_dotenv
import pygame
import keyboard
import time
load_dotenv()
pygame.mixer.init()

USE_ELEVENLABS_VOICE = True

import pvporcupine
import struct
import pyaudio

def listen_for_wake_word():
    """
    Listens in the background until the wake word is detected.
    """
    access_key = os.environ.get("PICOVOICE_ACCESS_KEY")
    keyword_path = "Bella.ppn"
    porcupine = None
    pa = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path] # Use keyword_paths for custom models
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("Listening for wake word...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected!")
                return # Exit the function once the wake word is heard

    finally:
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        if porcupine is not None:
            porcupine.delete()

def listen_for_command():
    """Listens for a command and transcribes it using Indian English model."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your command...")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-IN')
        print(f"You said: {query}\n")
        return query.lower()
    except Exception as e:
        return None
    
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
chat_session = genai.GenerativeModel('gemini-2.5-flash').start_chat(history=[])

def get_response_from_gemini(command):
    """Sends command to Gemini to extract intent and entities."""
    if not command:
        return None

    # This is a crucial prompt. It tells Gemini how to behave.
    prompt = f"""
    You are Bella, a general purpose bot. Analyze the following user command. Your primary goal is to determine if it matches a specific automation task.

    The possible task intents are: "send_email", "read_email", "delete_email", "login", "take_screenshot", "set_volume", "open_folder", "google_search", "get_news", "find_location", "get_weather", "lock_computer", "create_sticky_note", "convert_currency".
    If the command matches a task, your response MUST be a JSON object with "intent" and "entities".
    - For the "set_volume" intent, extract a "percentage" entity and treat the word "mute" as a percentage of "0".
    - For the "find_location" intent, extract a "location_name" entity.
    - For the "get_weather" intent, extract a "location" entity; if no location is mentioned, use "Mambakkam".
    - For the "create_sticky_note" intent, extract a "note_content" entity.
    - For the "convert_currency" intent, extract "amount", "from_currency", and "to_currency" entities.

    If the command is a general question, greeting, or statement that is NOT related to the specific tasks, you MUST classify it as "conversational".
    For a "conversational" intent, your role is to be a helpful and knowledgeable assistant. You should answer general questions directly and concisely.
    Your response MUST be a JSON object containing the key "intent" set to "conversational" and a new key "response" with your friendly, helpful text answer.
    Crucially, the "response" text MUST be plain text suitable for a text-to-speech engine. Do NOT use any markdown formatting like asterisks, backticks, hashes, or numbered lists.

    User command: "{command}"

    JSON Response:
    """

    try:
        response = chat_session.send_message(prompt)
        # Clean up the response to be valid JSON
        json_response = response.text.strip().replace('```json', '').replace('```', '')
        return json_response
    except Exception as e:
        print(f"Error contacting Gemini: {e}")
        return None

def sanitize_for_speech(text):
    """Removes common markdown symbols from text to make it TTS-friendly."""
    text = text.replace('*', '')  # Remove asterisks
    text = text.replace('`', '')  # Remove backticks
    text = text.replace('#', '')  # Remove hashes
    text = text.replace('_', '')  # Remove underscores
    return text 

import subprocess
import json

import subprocess

def execute_uipath_robot(intent_json_str):
    """
    Executes the UiPath process, correctly formatting the input arguments.
    """
    if not intent_json_str:
        speak("I couldn't understand the command.")
        return

    # --- Make sure these paths are correct for your system ---
    uipath_robot_exe = r"C:\Users\Tarun Parthiban\AppData\Local\Programs\UiPath\Studio\UiRobot.exe"
    process_name = "Bella_Assistant_Process"

    # --- THIS IS THE KEY CHANGE ---
    # Create a Python dictionary where the key matches the UiPath argument name
    uipath_arguments = {
        "in_CommandJson": intent_json_str
    }
    # Convert this final dictionary to the JSON string the robot needs
    final_input_json = json.dumps(uipath_arguments)
    # --- END OF CHANGE ---

    # Build the command list with the correctly formatted JSON
    command = [
        uipath_robot_exe,
        "execute",
        "--process-name",
        process_name,
        "--input",
        final_input_json  # Pass the new, correctly formatted payload
    ]

    print(f"Executing UiPath with payload: {final_input_json}") # Helpful for debugging
    
    subprocess.run(command)

from gtts import gTTS
import playsound
from elevenlabs.client import ElevenLabs
from elevenlabs import stream

# --- Define BOTH speak functions with different names ---

def speak_gtts(text):
    """Converts text to speech using Google's free TTS engine."""
    print(f"Assistant: {text}")
    try:
        tts = gTTS(text=text, lang='en-IN', tld='co.in') # Use Indian English accent
        audio_file = "response.mp3"
        tts.save(audio_file)
        playsound.playsound(audio_file)
        os.remove(audio_file)
    except Exception as e:
        print(f"Error in gTTS: {e}")

def speak_elevenlabs(text):
    """Converts text to speech using the high-quality ElevenLabs API."""
    print(f"Assistant: {text}")
    try:
        client = ElevenLabs(api_key=os.environ.get("ELEVEN_API_KEY"))
        audio_stream = client.text_to_speech.stream(
            text=text,
            voice_id="yM93hbw8Qtvdma2wCnJG", 
            model_id="eleven_multilingual_v2"
        )
        stream(audio_stream)
    except Exception as e:
        print(f"Error using ElevenLabs: {e}")

# --- Create a single "speak" function that chooses which to use ---

def speak(text):
    """
    Generates speech, plays it, allows interruption, and correctly cleans up the file.
    """
    print(f"Assistant: {text}")
    audio_file = "response.mp3"

    try:
        # --- Step 1: Generate the audio file (your existing logic) ---
        if USE_ELEVENLABS_VOICE:
            # ElevenLabs generation logic...
            client = ElevenLabs(api_key=os.environ.get("ELEVEN_API_KEY"))
            audio_stream = client.text_to_speech.stream(
                text=text,
                voice_id="yM93hbw8Qtvdma2wCnJG",
                model_id="eleven_multilingual_v2"
            )
            with open(audio_file, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
        else:
            # gTTS generation logic...
            tts = gTTS(text=text, lang='en-IN', tld='co.in')
            tts.save(audio_file)

        # --- Step 2: Play the audio with Pygame ---
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        # --- Step 3: Listen for interrupt ---
        while pygame.mixer.music.get_busy():
            if keyboard.is_pressed('right ctrl'):
                pygame.mixer.music.stop()
                print("--- Interrupted by user ---")
                break
            time.sleep(0.1)

    except Exception as e:
        print(f"Error in speak function: {e}")
    
    finally:
        # --- Step 4: Correctly clean up the audio file ---
        # Explicitly unload the music to release the file lock
        pygame.mixer.music.unload() 
        
        # A tiny delay to give the OS a moment to release the file
        time.sleep(0.1) 

        # Now it's safe to remove the file
        if os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except PermissionError:
                print(f"Could not delete {audio_file} as it's still in use.") 

def correct_email_with_gemini(raw_text):
    """
    Uses Gemini to correct a potentially garbled, spelled-out email address.
    """
    if not raw_text:
        return None

    print(f"Attempting to correct email from raw text: '{raw_text}'")
    
    # A specialized prompt for the correction task
    prompt = f"""
    Your task is to act as an expert email address corrector. Follow these rules in order.

    **Rule 1: Check the Priority List First**
    You have a priority list of known email addresses. Your first and most important job is to check if the user's transcribed input is a likely, even if misspelled, version of one of these emails.

    **Priority List:**
    * `tarunpr1103@gmail.com`
    * `benetajohnson24@gmail.com`

    If the input is a close match to one of the above, you **MUST** output the correct email from this priority list.

    **Rule 2: General Correction (Fallback)**
    **Only if the input is NOT a close match to the priority list**, you must use your general knowledge to correct it based on the following:
    * The user will spell out letters.
    * Common keywords: 'at' means '@', 'dot' means '.'.
    * The transcription may contain common single-letter errors (e.g., 'd' for 'b', 'm' for 'n').
    * You must remove all spaces.

    **Rule 3: Output Format**
    Your final response **MUST BE ONLY** the corrected email address and nothing else.

    ---
    **Examples:**

    * **Example of a Priority Match:**
        * Input: `"d a r u n p r one one o three at g mail"`
        * Output: `tarunpr1103@gmail.com`

    * **Example of a General Correction:**
        * Input: `"j o n snow ad outlook dot com"`
        * Output: `jonsnow@outlook.com`
    ---

    Now, correct the following input:
    Input: "{raw_text}"
    Output:
    """

    try:
        # We use the main model for this one-off task, not the chat session
        response = genai.GenerativeModel('gemini-2.5-flash').generate_content(prompt)
        corrected_email = response.text.strip()
        print(f"Gemini corrected email: {corrected_email}")
        return corrected_email
    except Exception as e:
        print(f"Error correcting email with Gemini: {e}")
        return raw_text # Fallback to the raw text if Gemini fails

def correct_text_with_gemini(raw_text, context_label="text"):
    """
    Uses Gemini to correct grammar, spelling, and punctuation from a voice transcription.
    """
    if not raw_text:
        return ""

    print(f"Attempting to correct {context_label} from raw text: '{raw_text}'")
    
    prompt = f"""
    You are an intelligent editor. Your task is to correct and reformat raw text transcribed from a user's voice.
    The text is for an '{context_label}'.
    Correct any spelling mistakes, fix grammatical errors, and add appropriate punctuation (like commas and periods).
    Preserve the original meaning of the text.
    Your response MUST BE ONLY the final, cleaned-up text and nothing else.

    Raw text: "{raw_text}"
    Corrected text:
    """

    try:
        # Use the main model for this one-off task
        response = genai.GenerativeModel('gemini-2.5-flash').generate_content(prompt)
        corrected_text = response.text.strip()
        print(f"Gemini corrected {context_label}: {corrected_text}")
        return corrected_text
    except Exception as e:
        print(f"Error correcting text with Gemini: {e}")
        return raw_text # Fallback to the raw text if Gemini fails

def handle_send_email_intent():
    """Guides the user through sending an email, using Gemini to correct the recipient."""
    
    speak("Who should I send the email to? Please spell it out.")
    recipient_raw = listen_for_command()
    if not recipient_raw:
        speak("I didn't hear an email address. Cancelling.")
        return

    # Use our new Gemini function to correct the email
    recipient = correct_email_with_gemini(recipient_raw)
    
    if not recipient:
        speak("I couldn't understand the email address. Cancelling the email.")
        return

    # The rest of the function remains the same
    speak(f"Okay, the recipient is {recipient}. What is the subject?")
    subject_raw = listen_for_command()
    subject = correct_text_with_gemini(subject_raw, "email subject")
    if not subject:
        speak("Sorry, I didn't get a subject. Cancelling the email.")
        return

    speak("And what should the message say?")
    body_raw = listen_for_command()
    body = correct_text_with_gemini(body_raw, "email body")
    if not body:
        speak("Sorry, I didn't get a message body. Cancelling the email.")
        return

    # --- Confirmation Step ---
    confirmation_prompt = f"So, I'm sending an email to {recipient} with the subject {subject}. The message is: {body}. Is that correct?"
    speak(sanitize_for_speech(confirmation_prompt))
    
    confirmation = listen_for_command()

    if confirmation and "yes" in confirmation:
        intent_data = {
            "intent": "send_email",
            "entities": {
                "recipient": recipient,
                "subject": subject,
                "body": body
            }
        }
        speak("Great, sending the email now.")
        intent_json_str = json.dumps(intent_data)
        execute_uipath_robot(intent_json_str)
    else:
        speak("Okay, I've cancelled the email.")

def main():
    """The main loop for the assistant."""
    speak("Assistant activated. Waiting for wake word.")

    # Outer loop: This runs forever, waiting for the wake word.
    while True:
        listen_for_wake_word()
        speak("Yes, how can I help?")

        # Inner loop: This is the active conversation session.
        # It will keep listening for commands until you say a dismiss phrase.
        while True:
            command = listen_for_command()

            if command:
                # Check for dismiss phrases to end the current conversation
                if any(phrase in command for phrase in ["goodbye", "that's all", "stop listening", "never mind", "back to sleep"]):
                    speak("Okay, going back to sleep. Let me know when you need me again.")
                    break  # This breaks the INNER loop, returning to the wake word loop.

                # --- Process the command as usual ---
                intent_json_str = get_response_from_gemini(command)
                print(f"Gemini Raw Response: {intent_json_str}")

                try:
                    intent_data = json.loads(intent_json_str)
                    intent = intent_data.get("intent")

                    if intent == "conversational":
                        reply = intent_data.get("response", "I'm not sure how to answer that.")
                        sanitized_reply = sanitize_for_speech(reply)
                        speak(sanitized_reply)
                    elif intent == "send_email":
                        handle_send_email_intent()
                        speak("Task complete. How can I help you next?") 
                    elif intent == "take_screenshot":
                        speak("Taking a screenshot now.")
                        intent_json_str = json.dumps(intent_data)  # Ensure it's a JSON string
                        execute_uipath_robot(intent_json_str)
                        speak("Task complete. How can I help you next?")
                    elif intent == "set_volume":
                        percentage = intent_data.get("entities", {}).get("percentage")
                        if percentage is not None:
                            speak(f"Setting volume to {percentage} percent.")
                            intent_json_str = json.dumps(intent_data)  # Ensure it's a JSON string
                            execute_uipath_robot(intent_json_str)
                            speak("Task complete. How can I help you next?")
                        else:
                            speak("I didn't catch the volume level. Please try again.")
                    elif intent == "get_news":
                        speak("Fetching the latest news.")
                        
                        # Define the specific output file for this task
                        output_file_path = r"C:\Tarun\College\Sem - 7\Theory\RPA\Project\Project Bella\headlines_output.txt"
                        
                        # Clean up old file before running
                        if os.path.exists(output_file_path):
                            os.remove(output_file_path)

                        # Call the generic robot executor
                        execute_uipath_robot(intent_json_str)
                        
                        # Now, handle the output specifically for the news task
                        headlines = ""
                        if os.path.exists(output_file_path):
                            with open(output_file_path, "r") as f:
                                headlines = f.read()
                            os.remove(output_file_path) # Clean up after reading
                        
                        if headlines:
                            speak("Here are the top 5 headlines")
                            speak(sanitize_for_speech(headlines))
                            speak("Task complete. How can I help you next?")
                        else:
                            speak("I couldn't fetch the news at this time.")
                    elif intent == "find_location":
                        location_name = intent_data.get("entities", {}).get("location_name")
                        if location_name:
                            speak(f"Finding the location of {location_name}.")
                            execute_uipath_robot(intent_json_str)
                        else:
                            speak("I didn't catch the location name. Please try again.")
                    elif intent == "get_weather":
                        speak("Let me check the weather for you.")
                        
                        # Define the specific output file for this task
                        output_file_path = r"C:\Tarun\College\Sem - 7\Theory\RPA\Project\Project Bella\weather_output.txt"
                        
                        if os.path.exists(output_file_path):
                            os.remove(output_file_path)

                        execute_uipath_robot(intent_json_str)
                        
                        weather_report = ""
                        if os.path.exists(output_file_path):
                            with open(output_file_path, "r") as f:
                                weather_report = f.read()
                            os.remove(output_file_path)
                        
                        if weather_report:
                            speak(sanitize_for_speech(weather_report))
                            speak("Task complete. How can I help you next?")
                        else:
                            speak("Sorry, I couldn't get the weather information.")
                    elif intent == "lock_computer":
                        speak("Locking the computer now.")
                        execute_uipath_robot(intent_json_str)
                        break
                    elif intent == "create_sticky_note":
                        speak("Okay, creating that sticky note for you.")
                        execute_uipath_robot(intent_json_str)
                    elif intent == "convert_currency":
                        speak("Looking up that currency conversion.")
                        
                        # Define the specific output file for this task
                        output_file_path = r"C:\Tarun\College\Sem - 7\Theory\RPA\Project\Project Bella\currency_output.txt"
                        
                        if os.path.exists(output_file_path):
                            os.remove(output_file_path)

                        execute_uipath_robot(intent_json_str)
                        
                        conversion_result = ""
                        if os.path.exists(output_file_path):
                            with open(output_file_path, "r") as f:
                                conversion_result = f.read()
                            os.remove(output_file_path)
                        
                        if conversion_result:
                            speak(sanitize_for_speech(conversion_result))
                        else:
                            speak("Sorry, I couldn't get the currency conversion information.")
                    elif intent == "read_email":
                        speak("Let me check your inbox for unread emails.")
                        
                        # Define the specific output file for this task
                        output_file_path = r"C:\Tarun\College\Sem - 7\Theory\RPA\Project\Project Bella\email_subjects_output.txt"
                        
                        if os.path.exists(output_file_path):
                            os.remove(output_file_path)

                        execute_uipath_robot(intent_json_str) # Pass the basic intent JSON
                        
                        email_subjects = ""
                        if os.path.exists(output_file_path):
                            with open(output_file_path, "r") as f:
                                email_subjects = f.read()
                            os.remove(output_file_path)
                        
                        if email_subjects:
                            speak(sanitize_for_speech(email_subjects))
                        else:
                            # This covers both errors and the "no unread emails" case
                            speak("Sorry, I couldn't retrieve unread email subjects.")
                    else:
                        speak("Sorry, I'm not sure how to handle that command.")

                except (json.JSONDecodeError, TypeError):
                    speak("I had trouble understanding the response format.")
            else:
                # If listen_for_command returns None (no speech detected)
                speak("I didn't hear anything. Is there anything else?")
                # After this, the inner loop will run again, listening for another command.


if __name__ == "__main__":
    main()