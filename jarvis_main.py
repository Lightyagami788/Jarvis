import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import subprocess
import os
import webbrowser
import time
from datetime import datetime
from pathlib import Path

GEMINI_API_KEY = "AIzaSyDtagAC7zSCMvimq9DWXkuYMuF3P_NyECY"
genai.configure(api_key=GEMINI_API_KEY)

def get_model():
    supported = []
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            supported.append(m.name)
    if not supported:
        raise RuntimeError("No models found that support generateContent. Check your API key and access.")
    print(f"Using Gemini model: {supported[0]}")
    return genai.GenerativeModel(supported[0])

model = get_model()
tts = pyttsx3.init()
recognizer = sr.Recognizer()

def speak(text):
    print(f"Jarvis: {text}")
    tts.say(text)
    tts.runAndWait()

def listen(prompt=""):
    with sr.Microphone() as source:
        if prompt:
            speak(prompt)
        print("Listening...")
        try:
            audio = recognizer.listen(source, phrase_time_limit=7, timeout=7)
            command = recognizer.recognize_google(audio)
            print(f"You: {command}")
            return command.lower()
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start")
            return ""
        except sr.UnknownValueError:
            print("Couldn't understand what you said")
            return ""
        except Exception as e:
            print(f"Error during listening: {e}")
            return ""

def query_gemini(prompt, history=None):
    chat_history = []
    if history:
        chat_history = [{"role": h["role"], "parts": [h["content"]]} for h in history]
    chat_history.append({"role": "user", "parts": [prompt]})

    response = model.generate_content(chat_history)
    if hasattr(response, "text"):
        return response.text.strip()
    elif hasattr(response, "candidates") and response.candidates:
        return response.candidates[0].content.parts[0].text.strip()
    else:
        return "I'm sorry, I couldn't process that."

def open_app(app_name):
    app_path = f"/Applications/{app_name}.app"
    if os.path.exists(app_path):
        subprocess.call(["open", app_path])
        speak(f"Opening {app_name}")
    else:
        result = subprocess.call(["open", "-a", app_name])
        if result == 0:
            speak(f"Opening {app_name}")
        else:
            speak(f"Sorry, I couldn't open {app_name}. Make sure the app name is correct and it's installed.")

def search_web(query):
    speak(f"Searching for {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")

def shutdown_mac():
    speak("Shutting down your MacBook. Goodbye!")
    os.system("sudo shutdown -h now")

def create_file(filename):
    Path(filename).touch()
    speak(f"File {filename} created.")

def get_time():
    now = datetime.now().strftime("%H:%M")
    speak(f"The time is {now}")

def execute_command(command, gemini_answer):
    if "open" in command:
        words = command.split()
        idx = words.index("open")
        app_name = " ".join(words[idx + 1:]).strip().title()
        if app_name:
            open_app(app_name)
            return
    elif "search" in command:
        query = command.partition("search")[-1]
        search_web(query)
    elif "shutdown" in command:
        shutdown_mac()
    elif "create file" in command:
        filename = command.split("file")[-1].strip()
        create_file(filename)
    elif "time" in command:
        get_time()
    elif "play music" in command:
        open_app("Music")
    elif "volume up" in command or "increase volume" in command:
        os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
        speak("Volume increased.")
    elif "volume down" in command or "decrease volume" in command:
        os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
        speak("Volume decreased.")
    elif "brightness" in command:
        level = ''.join(filter(str.isdigit, command))
        if level:
            os.system(f"brightness {int(level)/100.0}")
            speak(f"Brightness set to {level} percent.")
        else:
            speak("Specify brightness level from 0 to 100.")
    elif "exit" in command or "quit" in command or "bye" in command:
        speak("Goodbye, boss!")
        exit(0)
    else:
        speak(gemini_answer)

def main():
    speak("Hello, I am Jarvis made by Ameya. Say 'Hey Jarvis' to wake me up.")
    history = []
    # Calibrate for ambient noise once at startup
    with sr.Microphone() as source:
        print("Calibrating for ambient noise, please wait...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete.")

    while True:
        # Wake word loop
        while True:
            wake = listen()
            if wake and "hey jarvis" in wake:
                speak("Yes sir how may i help you ")
                break

        command = listen("How can I help you?")
        if not command:
            continue

        gemini_answer = query_gemini(command, history)
        history.append({"role": "user", "content": command})
        history.append({"role": "model", "content": gemini_answer})

        execute_command(command, gemini_answer)
        time.sleep(1)

if __name__ == "__main__":
    main()