from Frontend.GUI import (
    GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen,
    TempDirectoryPath, SetMicrophoneStatus, AnswerModifier,
    QueryModifier, GetMicrophoneStatus, GetAssistantStatus,
    GetEndButtonStatus, ResetEndButtonStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealTimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.CoderAgent import CoderAgent 
from Backend.ImageGeneration import GenerateImages
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import platform
import traceback
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
#==================================== System Control Functions ============================#
def shutdown_system():
    os_name = platform.system()
    if os_name == "Windows":
        os.system("shutdown /s /t 1")
    elif os_name in ["Linux", "Darwin"]:
        os.system("sudo shutdown now")
    else:
        print("Unsupported OS")

def restart_system():
    os_name = platform.system()
    if os_name == "Windows":
        os.system("shutdown /r /t 1")
    elif os_name in ["Linux", "Darwin"]:
        os.system("sudo reboot")
    else:
        print("Unsupported OS")
        
def lock_system():
    os_name = platform.system()
    if os_name == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif os_name == "Linux":
        os.system("gnome-screensaver-command -l")
    elif os_name == "Darwin":
        os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")
    else:
        print("Unsupported OS")

def sleep_system():
    os_name = platform.system()
    if os_name == "Windows":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif os_name == "Linux":
        os.system("systemctl suspend")
    elif os_name == "Darwin":
        os.system("pmset sleepnow")
    else:
        print("Unsupported OS")

# Environment Variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
DefaultMessage = f"""{AssistantName} : Welcome {Username}, I’m online and ready to help you."""


# Use a single consistent subprocess list name
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# GUI window reference and last Query (declare globals)
GUI_WINDOW = None
Query = ""

# STOP flags (global)
STOP_ALL_TASKS = False
STOP_LISTENING = False

#================================ Utility / Setup Functions ===============================#

def ShowDefaultChatIfNoChats():
    try:
        with open(resource_path(r'Data\ChatLog.json'), "r", encoding='utf-8') as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:
                    db_file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as resp_file:
                    resp_file.write(DefaultMessage)
    except FileNotFoundError:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:
            db_file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as resp_file:
            resp_file.write(DefaultMessage)


def ReachChatLogJson():
    with open(resource_path(r'Data\ChatLog.json'), 'r', encoding='utf-8') as file:
        return json.load(file)

def ChatLogIntegration():
    json_data = ReachChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        role = entry["role"]
        content = entry["content"]
        if role == "user":
            formatted_chatlog += f"User: {content}\n"
        elif role == "assistant":
            formatted_chatlog += f"Assistant: {content}\n"
    formatted_chatlog = formatted_chatlog.replace("User", f"{Username} ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", f"{AssistantName} ")
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowCharOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as File:
            Data = File.read()
        if len(str(Data)) > 0:
            lines = Data.split('\n')
            result = '\n'.join(lines)
            with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as File:
                File.write(result)
    except Exception as e:
        print(f"[ShowCharOnGUI ERROR] {e}")

def InitialExecution():
    """
    Run at startup. Keeps previous behavior but enables microphone after setup
    so the voice thread can start listening.
    """
    try:
        SetMicrophoneStatus("False")
        ShowTextToScreen("")
        # enable listening after initialization
        SetMicrophoneStatus("True")
        SetAssistantStatus("Listening...")
    except Exception as e:
        print(f"[InitialExecution ERROR] {e}")

#================================ Speech Helpers ================================#

def speak_and_listen(text: str):
    """
    Speaks text on a background thread. If it completes without interruption,
    it resets the assistant's state to "Listening...". The interruption
    logic is now primarily handled by handle_end_button.
    """
    def _worker():
        global STOP_ALL_TASKS
        try:
            # Pass a function that checks the global stop flag.
            # TTS will stop itself when the flag is True.
            TextToSpeech(text, func=lambda: not STOP_ALL_TASKS)
        except Exception as e:
            print(f"[TTS WORKER ERROR] {e}")
        finally:
            # IMPORTANT: Only reset the status if the task was NOT interrupted.
            # If it was interrupted, handle_end_button is in charge of the state.
            if not STOP_ALL_TASKS:
                try:
                    SetAssistantStatus("Listening...")
                    SetMicrophoneStatus("True")
                    print("[INFO] TTS completed normally — assistant reset to Listening.")
                except Exception as e:
                    print(f"[TTS finally-block ERROR] {e}")

    threading.Thread(target=_worker, daemon=True).start()

#============================== Task / Session Control ==============================#

def handle_end_button():
    """
    Immediately stops all running tasks. The order of operations is critical
    for a smooth and responsive user experience.
    """
    global subprocesses, Query, STOP_ALL_TASKS

    print("[INFO] End button triggered. Interrupting all tasks...")

    # 1. Raise the global stop flag immediately.
    # This signals all threads and loops to terminate gracefully.
    STOP_ALL_TASKS = True

    # 2. Stop audio output immediately.
    # This provides instant feedback to the user that their action was received.
    try:
        from pygame import mixer
        if mixer.get_init():
            mixer.music.stop()   # stop playback immediately
            mixer.quit()         # release audio device
    except Exception as e:
        print(f"[handle_end_button mixer ERROR] {e}")

    # 3. Kill any spawned subprocesses (e.g., automation scripts, image viewers).
    for proc in subprocesses:
        try:
            proc.kill()
        except Exception:
            pass  # Process might have already finished
    subprocesses.clear()

    # 4. Update the GUI to reflect the new state.
    # Do this after stopping tasks so the UI shows the final, correct state.
    try:
        SetMicrophoneStatus("True")  # Re-enable the microphone for the next command.
        SetAssistantStatus("Listening...")
        ShowTextToScreen(f"{AssistantName} : All tasks stopped. How can I help you now?")
        ResetEndButtonStatus()
    except Exception as e:
        print(f"[handle_end_button UI reset ERROR] {e}")

    # 5. Clear the last query to prevent it from being re-processed.
    Query = ""

    # 6. Finally, reset the stop flag AFTER a tiny delay.
    # This ensures all tasks have processed the initial 'True' flag
    # and the system is ready for a new command.
    # The sleep is a small safety margin.
    sleep(0.1)
    STOP_ALL_TASKS = False
    print("[INFO] System reset and ready for new command.")

#========================== Main Assistant Logic (single, query-accepting function) ==========================#

def MainExecution(Query: str):
    """Main assistant logic function. Accepts a user query string and processes it."""
    global STOP_ALL_TASKS

    # If an end/stop has been requested, bail out immediately
    if STOP_ALL_TASKS:
        return

    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    # Show the user's query immediately on GUI (ensures instant feedback)
    try:
        ShowTextToScreen(f"{Username} : {Query}")
    except Exception:
        pass

    SetAssistantStatus("Thinking...")

    try:
        Decision = FirstLayerDMM(Query)
    except Exception as e:
        print(f"[MainExecution Decision ERROR] {e}")
        Decision = []

    if STOP_ALL_TASKS:
        return

    print(f"\nDecision : {Decision}\n")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)
    Mearged_query = " and ".join(
        " ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")
    )

    # Image Generation
    for queries in Decision:
        if STOP_ALL_TASKS:
            return
        if "generate" in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    # Automation
    for queries in Decision:
        if STOP_ALL_TASKS:
            return
        if not TaskExecution and any(queries.startswith(func) for func in Functions):
            try:
                run(Automation(list(Decision)))
            except Exception as e:
                print(f"[Automation ERROR] {e}")
            TaskExecution = True

    if STOP_ALL_TASKS:
        return

    # spawn image process
    if ImageExecution:
        try:
            prompt = ImageGenerationQuery.replace("generate ", "").strip()
            files = GenerateImages(prompt)  # <-- returns list of files

            if files and all(os.path.exists(f) for f in files):
                ShowTextToScreen(f"{AssistantName} : Images generated successfully. Please check them on your screen, sir.")
                SetAssistantStatus("Answering...")
                speak_and_listen("Images generated successfully. Please check them on your screen, sir.")
            else:  # failed
                ShowTextToScreen(f"{AssistantName} : Sorry, I was unable to generate the images.")
                SetAssistantStatus("Answering...")
                speak_and_listen("Sorry, I was unable to generate the images.")

        except Exception as e:
            print(f"[ImageGeneration ERROR] {e}")
            ShowTextToScreen(f"{AssistantName} : Sorry, I was unable to generate the images.")
            SetAssistantStatus("Answering...")
            speak_and_listen("Sorry, I was unable to generate the images.")

    if STOP_ALL_TASKS:
        return

    # real-time search
    if G and R or R:
        SetAssistantStatus("Searching...")
        try:
            Answer = RealTimeSearchEngine(QueryModifier(Mearged_query))
        except Exception as e:
            print(f"[RealTimeSearchEngine ERROR] {e}")
            Answer = "Sorry, I couldn't retrieve real-time info."
        try:
            ShowTextToScreen(f"{AssistantName} : {Answer}")
        except Exception:
            pass

        if STOP_ALL_TASKS:
            return

        SetAssistantStatus("Answering...")
        speak_and_listen(Answer)
        return True

    # Other decisions
    for Queries in Decision:
        if STOP_ALL_TASKS:
            return
        try:
                            
            if "shutdown" in Queries.lower():
                confirm_msg = "Are you sure you want to shut down the system? Please say yes or no."
                ShowTextToScreen(f"{AssistantName} : {confirm_msg}")
                SetAssistantStatus("Confirming...")
                speak_and_listen(confirm_msg)
                confirmation = SpeechRecognition().lower()
                if "yes" in confirmation:
                    speak_msg = "System will shut down now."
                    ShowTextToScreen(f"{AssistantName} : {speak_msg}")
                    SetAssistantStatus("Answering...")
                    speak_and_listen(speak_msg)
                    shutdown_system()
                else:
                    speak_msg = "Shutdown canceled."
                    ShowTextToScreen(f"{AssistantName} : {speak_msg}")
                    SetAssistantStatus("Answering...")
                    speak_and_listen(speak_msg)
                return True

            elif "restart" in Queries.lower():
                confirm_msg = "Are you sure you want to restart the system? Please say yes or no."
                ShowTextToScreen(f"{AssistantName} : {confirm_msg}")
                SetAssistantStatus("Confirming...")
                speak_and_listen(confirm_msg)
                confirmation = SpeechRecognition().lower()
                if "yes" in confirmation:
                    speak_msg = "System will restart now."
                    ShowTextToScreen(f"{AssistantName} : {speak_msg}")
                    SetAssistantStatus("Answering...")
                    speak_and_listen(speak_msg)
                    restart_system()
                else:
                    speak_msg = "Restart canceled."
                    ShowTextToScreen(f"{AssistantName} : {speak_msg}")
                    SetAssistantStatus("Answering...")
                    speak_and_listen(speak_msg)
                return True

            elif "lock" in Queries.lower():
                lock_system()
                speak_msg = "System is locked."
                ShowTextToScreen(f"{AssistantName} : {speak_msg}")
                SetAssistantStatus("Answering...")
                speak_and_listen(speak_msg)
                return True

            elif "sleep" in Queries.lower():
                sleep_system()
                speak_msg = "System is going to sleep."
                ShowTextToScreen(f"{AssistantName} : {speak_msg}")
                SetAssistantStatus("Answering...")
                speak_and_listen(speak_msg)
                return True

            elif "general" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general ", "")
                try:
                    Answer = ChatBot(QueryModifier(QueryFinal))
                except Exception as e:
                    print(f"[ChatBot ERROR] {e}")
                    Answer = "Sorry, I couldn't compute that right now."

                if STOP_ALL_TASKS:
                    return

                ShowTextToScreen(f"{AssistantName} : {Answer}")
                SetAssistantStatus("Answering...")
                speak_and_listen(Answer)
                return True

            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime ", "")
                try:
                    Answer = RealTimeSearchEngine(QueryModifier(QueryFinal))
                except Exception as e:
                    print(f"[RealTimeSearchEngine ERROR] {e}")
                    Answer = "Sorry, I couldn't retrieve real-time info."

                if STOP_ALL_TASKS:
                    return

                ShowTextToScreen(f"{AssistantName} : {Answer}")
                SetAssistantStatus("Answering...")
                speak_and_listen(Answer)
                return True
            
            elif "coder" in Queries or "debug" in Queries or "review" in Queries or "write" in Queries:
                agent = CoderAgent()
                Answer = agent.handle(Query)
                ShowTextToScreen(f"{AssistantName} : {Answer}")
                if GUI_WINDOW:
                    GUI_WINDOW.show_text(f"{AssistantName} : {Answer}")
                SetAssistantStatus("Answering...")
                speak_and_listen(Answer)
                return True

            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{AssistantName} : {Answer}")
                SetAssistantStatus("Answering...")
                speak_and_listen(Answer)
                os._exit(1)
        except Exception as e:
            print(f"[MainExecution inner ERROR] {e}\n{traceback.format_exc()}")

    # Always reset mic + status at the end (if not interrupted)
    try:
        if not STOP_ALL_TASKS:
            SetAssistantStatus("Listening...")
            SetMicrophoneStatus("True")
    except Exception as e:
        print(f"[MainExecution reset ERROR] {e}")

#============================= Unified Query Processor =============================#

def process_query(query: str):
    """Processes a user query by running the main assistant logic with the given query."""
    global Query, STOP_ALL_TASKS, STOP_LISTENING

    # Starting a new user query resets stop-listen so it can run
    STOP_ALL_TASKS = False
    STOP_LISTENING = False

    if not query or not str(query).strip():
        return
    Query = query
    
    try:
        SetAssistantStatus("Processing...")
        SetMicrophoneStatus("False")
        MainExecution(query)
    except Exception as e:
        print(f"[process_query ERROR] {e}\n{traceback.format_exc()}")
        SetAssistantStatus("Listening...")
        SetMicrophoneStatus("True")

# Threads
def VoiceThread():
    """Continuously listens for commands."""
    global STOP_ALL_TASKS

    while True:
        # Check for the end button status at the very start of the loop
        if GetEndButtonStatus():
            handle_end_button()
            continue # Restart the loop immediately after handling the stop

        try:
            # Only listen if the mic is enabled AND no stop signal is active
            if GetMicrophoneStatus() == "True" and not STOP_ALL_TASKS:
                Query_spoken = "" # Reset before listening
                try:
                    Query_spoken = SpeechRecognition()
                except Exception as e:
                    print(f"[VoiceThread SpeechRecognition ERROR] {e}")

                if Query_spoken and not STOP_ALL_TASKS:
                    # Normalize the speech
                    spoken = Query_spoken.strip().lower()

                # If user says "stop" or "cancel", immediately trigger end button
                if spoken in ["stop", "cancel"]:
                    print("[VOICE] Stop command detected — interrupting tasks.")
                    handle_end_button()
                else:
                    process_query(Query_spoken)


            else:
                # If not listening, just yield control to other threads briefly
                sleep(0.1)

        except Exception as e:
            print(f"[VoiceThread outer ERROR] {e}\n{traceback.format_exc()}")
            sleep(0.1) # Avoid busy-looping on error

def GUIThread():
    """Starts GUI and binds input box to same processor"""
    global GUI_WINDOW, STOP_ALL_TASKS, STOP_LISTENING
    GUI_WINDOW = GraphicalUserInterface()

    # hook end button (GUI end button will call SetEndButtonStatus internally)
    try:
        GUI_WINDOW.end_button.clicked.connect(handle_end_button)
    except Exception:
        pass

    # text input hook: depending on widget type (QLineEdit/QTextEdit)
    def handle_text_input():
        nonlocal_gui = False
        query = ""
        try:
            if hasattr(GUI_WINDOW.chat_screen.input_box, "text"):
                query = GUI_WINDOW.chat_screen.input_box.text().strip()
            elif hasattr(GUI_WINDOW.chat_screen.input_box, "toPlainText"):
                query = GUI_WINDOW.chat_screen.input_box.toPlainText().strip()
        except Exception:
            query = ""

        if query:
            # clear the appropriate widget
            try:
                if hasattr(GUI_WINDOW.chat_screen.input_box, "clear"):
                    GUI_WINDOW.chat_screen.input_box.clear()
            except Exception:
                pass

            # When user enters text, reset stop flags so this new query runs
            STOP_ALL_TASKS = False
            STOP_LISTENING = False

            
            process_query(query)

    # connect safely (ignores errors if widget API differs)
    try:
        GUI_WINDOW.chat_screen.input_box.returnPressed.connect(handle_text_input)
    except Exception:
        # some input widgets may be QTextEdit (no returnPressed) — we still connect Send button below
        pass
    try:
        GUI_WINDOW.chat_screen.send_button.clicked.connect(handle_text_input)
    except Exception:
        pass

#============================= Entry Point =============================#
if __name__ == "__main__":
    InitialExecution()
    threading.Thread(target=VoiceThread, daemon=True).start()
    GUIThread() 
