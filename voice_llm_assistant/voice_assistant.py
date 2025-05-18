import openai
import speech_recognition as sr
import pyttsx3
import os

openai.api_key = "API_KEY"  

recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()

def speak(text):
    print("Assistant:", text)
    tts_engine.say(text)
    tts_engine.runAndWait()

def get_audio():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't understand that."
        except sr.RequestError:
            return "Speech recognition service is unavailable."

def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def handle_voice_command():
    query = get_audio()
    if "sorry" in query.lower() or "unavailable" in query.lower():
        speak(query)
        return query
    response = ask_openai(query)
    speak(response)
    return response
