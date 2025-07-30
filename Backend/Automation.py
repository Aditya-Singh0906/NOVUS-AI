# Import required libraries
from AppOpener import close, open as appopen # import function to open and close apps
from webbrowser import open as webopen  # import web browser functionality
from pywhatkit import search, playonyt  # import functions for google search and youtube playback
from dotenv import dotenv_values  # import dotenv to manage environment variables
from bs4 import BeautifulSoup  # import BeautifulSoup for HTML parsing
from rich import print  # import rich for styled console output
from groq import Groq  # import Groq for AI chat functionalities
from serpapi import GoogleSearch  # import SerpAPi
import webbrowser  # import webbrowser for opening URLs
import subprocess  # import subprocess for interacting with the system
import requests   # import requests for making HTTP requests
import keyboard  # import keyboard for keyboard related actions
import asyncio  # import asyncio for asynchronous programming
import os  # import os for operating system functionalitis
from urllib.parse import unquote  # import unquote for URL decoding

# Load environment variables from the .env files
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")  # retrieve the Groq API key

# define CSS classes for parsing specific elements in HTML content
Classes = [
    "zCubuf", "hgKELc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee",
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
            model="llama3-70b-8192",   # specify the AI model
            messages=SystemChatBot + messages,   # include system instructions and chat history
            max_tokens=2048,  # limit the maximum tokens in the response
            temperature=0.7,  # adjust response randomness
            top_p=1,  # use nucleus sampling for response diversity
            stream=True,  # enable streaming for response
            stop=None   # allow the model to determine stopping conditions
        )
        
        Answer = ""  # initalize an empty string for the response
        
        # process streamed response chunks
        for chunk in completion:
            if chunk.choices[0].delta.content:  # check for content in the current chunk
               Answer += chunk.choices[0].delta.content # append the content to the answer
               
        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer


    Topic: str = Topic.replace("Content ", "") # remove "Content" from the topic
    ContentByAI = ContentWriterAI(Topic)  # Generate content using the AI chatbot
    
    # save the generated content to a text file
    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
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

# function to open an application or a relevant webpage
def OpenApp(app, sess=requests.session()):
    try:
        # Attempt to open using AppOpener
        from AppOpener import open as appopen
        appopen(app.lower(), match_closest=True, output=True, throw_error=True)
        print(f"✅ Opened desktop app: {app}")
        return True

    except Exception as e:
        print(f"⚠️ App not found: {app}, falling back to web/manual search...")

        # Manual fallback for known simple apps
        known_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "wordpad": "write.exe",
            "command prompt": "cmd.exe"
        }

        if app.lower() in known_apps:
            try:
                subprocess.Popen(known_apps[app.lower()])
                print(f"✅ Manually opened: {app}")
                return True
            except Exception as e:
                print(f"❌ Manual fallback failed for {app}: {e}")

        # Function to extract website links from HTML
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            for a in soup.select("li.b_algo h2 a"):
                href = a.get('href')
                if href and href.startswith("http"):
                    links.append(href)
            return links


        # Bing search fallback (more reliable than Google for scraping)
        def search_web(query):
            url = f"https://www.bing.com/search?q={query}"
            headers = {
                "User-Agent": useragent,
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                response = sess.get(url, headers=headers, timeout=5)
                print(f"🔍 Bing Response Status: {response.status_code}")
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"❌ Bing search failed with status code: {response.status_code}")
                    return None
            except Exception as e:
                print(f"❌ Exception during web search: {e}")
                return None

        # Perform web fallback
        html = search_web(app)
        if html:
            links = extract_links(html)
            if links:
                print(f"🌐 Opening web version of: {app}")
                webbrowser.open(links[0])
            else:
                print(f"❌ No valid website found for: {app}")
        return True

# function to close an application
def CloseApp(app):
    
    if "chrome" in app:
        pass # skip if the app is chrome
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)  # attempt to close the app
            return True
        except:
            return False
     
# function to execute system-level commands       
def System(command):
    
    # nested function to mute the system volume
    def mute():
        keyboard.press_and_release("volume mute")  # simulate the mute key press
    
    # nested function to unmute the system volume
    def unmute():
        keyboard.press_and_release("volume mute")  # simulate the unmute key press
  
    # nested function to volume up the system volume
    def volume_up():
        keyboard.press_and_release("volume up")    # simulate the uvolume up key press
        
    # nested function to volume down the system volume
    def volume_down():
        keyboard.press_and_release("volume down")   # simulate the volume down key press

    # execute the appropriate command
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

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
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))  # schedule app opening
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
