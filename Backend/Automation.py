# Import required libraries
from AppOpener import close, open as appopen # import function to open and close apps
from webbrowser import open as webopen  # import web browser functionality
from pywhatkit import search, playonyt  # import functions for google search and youtube playback
from dotenv import dotenv_values  # import dotenv to manage environment variables
from bs4 import BeautifulSoup  # import BeautifulSoup for HTML parsing
from rich import print  # import rich for styled console output
from groq import Groq  # import Groq for AI chat functionalities
import webbrowser  # import webbrowser for opening URLs
import subprocess  # import subprocess for interacting with the system
import requests   # import requests for making HTTP requests
import keyboard  # import keyboard for keyboard related actions
import asyncio  # import asyncio for asynchronous programming
import os  # import os for operating system functionalitis
import platform  # import platform to identify the operating system
from AppOpener import open as appopen
from AppOpener.features import AppNotFound
import win32com.client
import psutil
import signal
from Backend.Utils import resource_path


# Load environment variables from the .env files
env_path = resource_path(".env")
env_vars = dotenv_values(env_path)

GroqAPIKey = env_vars.get("GroqAPIKey")  # retrieve the Groq API key

# define CSS classes for parsing specific elements in HTML content
Classes = [
    "zCubwf", "hgKELc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee",
    "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "O5uR6d LTKOO", "VlzY6d",
    "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLaOe",
    "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

# define a user-agent for making web requests
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# predefined professional responses for user interactions
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask."
]

# list to store chatbot messages
messages = []

# system message to provide context to the chatbot
SystemChatBot = [{"role": "system","content": f"Hello, I am {os.environ['Username']}, You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems etc."}]

# function to perform a Google search
def GoogleSearch(Topic):
    search(Topic)  # use pywhatkit to perform a Google search
    return True

# function to generate content using AI and save it to a file
def Content(Topic):

    # Nested function to open file in notepad
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File]) # open the file in notepad

    # nested function to generate content using the AI chatbot
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})  # add the user's prompt to message
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # specify the AI model
            messages=SystemChatBot + messages,   # include system instructions and chat history
            max_tokens=2048,  # limit the maximum tokens in the response
            temperature=0.7,  # adjust response randomness
            top_p=1,  # use nucleus sampling for response diversity
            stream=False,  # enable streaming for response
            stop=None   # allow the model to determine stopping conditions
        )
        
        Answer = ""  # initalize an empty string for the response
        
        Answer = completion.choices[0].message.content.strip()
               
        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer


    Topic: str = Topic.replace("Content ", "") # remove "Content" from the topic
    ContentByAI = ContentWriterAI(Topic)  # Generate content using the AI chatbot
    
    # save the generated content to a text file
    with open(resource_path(rf"Data\{Topic.lower().replace(' ', '')}.txt"), "w", encoding="utf-8") as file:
        file.write(ContentByAI)  # write the content to the file
        file.close()
        
    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt")  # open the file in notepad
    return True

# function to search for a topic on Youtube
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}" # create the url for the search
    webbrowser.open(Url4Search)  # open the search URL in a web browser
    return True

# function to play a video on YouTube
def PlayYoutube(query):
    playonyt(query)  # use pywhatkit playonyt function to play the video
    return True


def build_app_cache():
    app_index = {}

    search_paths = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",  # All users apps
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"),  # User apps
        os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"),  # User startup apps
        os.path.expanduser(r"~\Desktop"),  # Desktop
        os.path.expanduser(r"~\Documents"),  # Documents
        os.path.expanduser(r"~\Downloads"),  # Downloads
        r"D:\Santosh - Personal",  # OneDrive personal folder
    ]

    for path in search_paths:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".lnk") or file.endswith(".exe"):
                    name = os.path.splitext(file)[0].lower()
                    full_path = os.path.join(root, file)
                    app_index[name] = full_path
    return app_index


WEB_APPS = {
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "whatsapp": "https://web.whatsapp.com",
    "skype": "https://web.skype.com",
    "telegram": "https://web.telegram.org",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "linkedin": "https://www.linkedin.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "outlook": "https://outlook.live.com",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "flipkart": "https://www.flipkart.com",
    "snapchat": "https://web.snapchat.com",
    "discord": "https://discord.com",
    "zoom": "https://zoom.us"
}

system_apps = {
    "notepad": r"C:\Windows\System32\notepad.exe",
    "paint": r"explorer.exe shell:appsFolder\Microsoft.Paint_8wekyb3d8bbwe!App",  
    "calculator": "calc.exe",
    "camera": r"explorer.exe shell:appsFolder\Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
    "teams": r"C:\Users\singh\AppData\Local\Microsoft\Teams\Update.exe --processStart Teams.exe",
    "onenote": r"C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE",
    "photos": r"explorer.exe shell:appsFolder\Microsoft.Windows.Photos_8wekyb3d8bbwe!App",
    "calendar": r"explorer.exe shell:appsFolder\microsoft.windowscommunicationsapps_8wekyb3d8bbwe!microsoft.windowslive.calendar",
    "zoom": r"C:\Users\singh\AppData\Roaming\Zoom\bin\Zoom.exe"
}

folder_index = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "music": os.path.join(os.path.expanduser("~"), "Music"),
    "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    "projects": os.path.join(os.path.expanduser("~"), "Projects"),
    "personal": r"D:\Santosh - Personal",  # easy shortcut for your OneDrive
}


APP_CACHE = build_app_cache()
APP_CACHE.update(system_apps)   # merge system apps into cache


def open_item(query: str):
    query = query.lower().strip()

    # 1. Check in system/app cache
    if query in APP_CACHE:
        path = APP_CACHE[query]
        try:
            subprocess.Popen(path, shell=True)
            return f"Opening {query}"
        except Exception as e:
            return f"Couldn't open {query}: {str(e)}"

    # 2. Check in folder cache
    if query in folder_index:
        folder_path = folder_index[query]
        if os.path.exists(folder_path):
            os.startfile(folder_path)
            return f"Opening {query} folder"
        else:
            return f"Folder {query} not found"

    # 3. If query is a valid path (dynamic folder/file opening)
    if os.path.exists(query):
        os.startfile(query)
        return f"Opening {query}"

    # 4. Check in web apps
    if query in WEB_APPS:
        webbrowser.open(WEB_APPS[query])
        return f"Opening {query} website"

    # 5. Default fallback → Google search
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Searching {query} on Google..."


# function to close an application
def CloseApp(app_name: str):
    """
    Attempts to close an app or folder by process name or window title.
    Returns True if closed successfully, otherwise False.
    """
    app_name = app_name.lower().strip()

    # Handle folders separately (close Explorer windows)
    if "folder" in app_name or app_name.endswith(":") or "\\" in app_name or "/" in app_name:
        try:
            os.system("taskkill /f /im explorer.exe")
            os.system("start explorer.exe")  # restart Explorer after killing
            return True
        except Exception as e:
            print(f"Error closing folder: {e}")
            return False

    # Try closing app by process name
    closed = False
    for proc in psutil.process_iter(['name']):
        try:
            if app_name in proc.info['name'].lower():
                proc.terminate()  # graceful close
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # If not closed, try force killing
    if not closed:
        for proc in psutil.process_iter(['name']):
            try:
                if app_name in proc.info['name'].lower():
                    os.kill(proc.pid, signal.SIGKILL)  # force kill
                    closed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    return closed
     
# function to execute system-level commands       
def System(command):
    
    # nested function to mute the system volume
    def mute():
        keyboard.press_and_release("volume mute")  # simulate the mute key press
    
    # nested function to unmute the system volume
    def unmute():
        keyboard.press_and_release("volume unmute")  # simulate the unmute key press
  
    # nested function to volume up the system volume
    def volume_up():
        keyboard.press_and_release("volume up")    # simulate the uvolume up key press
        
    # nested function to volume down the system volume
    def volume_down():
        keyboard.press_and_release("volume down")   # simulate the volume down key press
        
    def play_pause():
        keyboard.press_and_release("play/pause media")   # simulate the play/pause key press
        
    def next_track():
        keyboard.press_and_release("next track")   # simulate the next track key press
    
    def previous_track():
        keyboard.press_and_release("previous track")   # simulate the previous track key press
        
    def stop_media():
        keyboard.press_and_release("stop media")   # simulate the stop media key press
        
    

    # execute the appropriate command
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    elif command == "play" or command == "play/pause":
        play_pause()
    elif command == "next" or command == "next track":
        next_track()    
    elif command == "previous" or command == "previous track":
        previous_track()
    elif command == "stop" or command == "stop media":
        stop_media()
    else:
        print(f"No system function found for command: {command}")

    return True

# asynchronous function to translate and execute user commands
async def TranslateAndExecute(commands: list[str]):
    
    funcs = []    # list to store asynchronous tasks
    
    for command in commands:
        
        if command.startswith("open "):  # handle "open" commands
            
            if "open it" in command:  # ignore "open it" commands
                pass
            
            if "open file" == command:  # ignore "open file" commands
                pass
            
            else:
                fun = asyncio.to_thread(open_item, command.removeprefix("open "))  # schedule app opening
                funcs.append(fun)
                
        elif command.startswith("general "):  # placeholder for general commands
            pass
        
        elif command.startswith("realtime "):  # placeholde for real-time commands
            pass
        
        elif command.startswith("close "):  # handle "close" commands
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))  # schedule app closing
            funcs.append(fun)
            
        elif command.startswith("play "):  # handle "play" commands
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))  # schedule YouTube playback
            funcs.append(fun)
            
        elif command.startswith("content "):  # handle "content" commands
            fun = asyncio.to_thread(Content, command.removeprefix("content "))  # schedule content creation
            funcs.append(fun)
            
        elif command.startswith("google search "):  # handle "google search" commands
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))  # schedule google search
            funcs.append(fun)
            
        elif command.startswith("youtube search "):  # handle "youtube search" commands
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search "))  # schedule YouTube search
            funcs.append(fun)
            
        elif command.startswith("system "):  # handle "system" commands
            fun = asyncio.to_thread(System, command.removeprefix("system "))  # schedule system command
            funcs.append(fun)
            
        else:
            print(f"No Function Found. For {command}")  # print an error

    results = await asyncio.gather(*funcs)  # execute all tasks concurrently
    
    for result in results:
        if isinstance(result, str):
            yield result
        else:
            yield result
             
# asynchronous function to automate command execution
async def Automation(commands: list[str]):
    
    async for result in TranslateAndExecute(commands):  # translate and execute commands
        pass
    
    return True    # Indicate Success