from groq import Groq    # importing Groq library for AI services
from json import load, dump   # importing functions to read and write JSON data
import datetime     # importing datetime module to work with dates and times information
from dotenv import dotenv_values    # importing dotenv to load environment variables from .env file

# Load environment variables from .env file
env_vars = dotenv_values(".env")

# Retrieve specific environment variables for username, assistant name, and Groq API key
Username = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
GroqAPIKey = env_vars.get("GroqAPIKey")

# intialize a Groq client using the API key
client = Groq(api_key=GroqAPIKey)

# intialize a empty list to store chat messages
messages = []

# define a system message that provides context to the AI modeland its role and behavior
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

# a list of system instructions for the chatbot
SystemChatBot = [
    {"role": "system", "content": System},
]

# attempt to load the chat log from a JSON file
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f) # load existing chat messages from the chat log
except FileNotFoundError:
    # if the file doesn't exist, create an empty json file to store chat logs
    with open(r"Data\ChatLog.json", "w") as f:
       dump([], f)  

# function to get real time date and time information
def RealtimeInformation():
   current_date_time = datetime.datetime.now()  # get the current date and time
   day = current_date_time.strftime("%A")  # get the current day of the week
   date = current_date_time.strftime("%d")  # get the current day of the month
   month = current_date_time.strftime("%B")  # get the current month
   year = current_date_time.strftime("%Y")  # get the current year
   hour = current_date_time.strftime("%H")  # get the current hour in 24-hour format
   minute = current_date_time.strftime("%M")  # get the current minute
   second = current_date_time.strftime("%S")  # get the current second

   # format the date and time information into a string
   data = f"Please use this real-time information if needed,\n"
   data += f"Day: {day}\n Date: {date}\n Month: {month}\n Year: {year}\n"
   data += f"Time: {hour} hours : {minute} minutes : {second} seconds\n"
   return data  

# function to modify the chatbot's response for better formatting
def AnswerModifier(Answer):
    lines = Answer.split("\n")  # split the answer into lines
    non_empty_lines = [line for line in lines if line.strip()]  # filter out empty lines
    modified_answer = "\n".join(non_empty_lines)  # join the non-empty lines
    return modified_answer  # return the modified answer

# Main chatbot function to handle user queries
def ChatBot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response."""
    try:
        # load the existing chat log from the JSON file
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)  

        # append the user's query to the messages list
        messages.append({"role": "user", "content": f"{Query}"})

        # make a request to the Groq API for a response
        completion = client.chat.completions.create(
            model="llama3-70b-8192",  # specify the model to use
            messages=SystemChatBot + [{"role": "user", "content": RealtimeInformation()}] + messages,  # include system instructions, real-time info and chat history
            max_tokens=1024,  # set the maximum number of tokens for the response
            temperature=0.7,  # adjust response randomness (higher means more random)
            top_p=1.0,  # set the nucleus sampling parameter
            stream=True,  # enable streaming for real-time response
            stop=None # allow the model to determine when to stop
        )

        Answer = ""  # initialize an empty string to store the response AI's response

        # process the streamed response chunks
        for chunk in completion:
            if chunk.choices[0].delta.content:  # check if there's content in the current chunk
                Answer += chunk.choices[0].delta.content  # append the content to the answer string

        Answer = Answer.replace("</s>", "")  # clean up any unwanted tokens from the response

        # append the chatbot's response to the messages list
        messages.append({"role": "assistant", "content": Answer})

        # save the updated chat log back to the JSON file
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        # return the formatted response
        return AnswerModifier(Answer=Answer)
    
    except Exception as e:
        # handle errors by printing the exception and resetting the chat log
        print(f"Error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)  # retry the query after resetting the chat log
    
# Main program entry point
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ") # prompt the user for a question
        print(ChatBot(user_input)) # call the chatbot function and print its response





   
