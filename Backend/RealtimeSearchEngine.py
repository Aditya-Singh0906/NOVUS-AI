from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# retrieve environment variables for the chatbot configuration
Username = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize a Groq client using the provided API key.
client = Groq(api_key=GroqAPIKey)

# define the system instructions for the chatbot
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# try to load the chat log from a JSON file, or create an empty log if it doesn't exist
try:
    with open('chat_log.json', 'r') as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# function to perform a google search and format the results
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))  
    Answer = f"The search results for '{query}' are:\n[start]\n"

    for i in results:
        Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
    
    Answer += "[end]"
    return Answer

# function to clean up the answer by removing empty lines
def AnswerModifier(Answer):
    lines = Answer.split("\n")  
    non_empty_lines = [line for line in lines if line.strip()]  # filter out empty lines
    modified_answer = "\n".join(non_empty_lines)  # join the non-empty lines
    return modified_answer  # return the modified answer

# predefined chatbot conversations system messages and an initial user message
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": f"Hello, how can I help you?"}
]

# function to get real-time information like current date and time
def Information():
    data = ""
    current_date_time = datetime.datetime.now()  
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f" Use This Real-time Information if needed,\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours : {minute} minutes : {second} seconds\n"
    return data

# function to handle real-time search and response generation
def RealTimeSearchEngine(prompt):
    global SystemChatBot, messages

    # load the chat log from the JSON file
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
    messages.append({"role": "user", "content": f"{prompt}"})

    # add google search results to the system chatbot messages
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    # generate a response using the Groq model
    completion = client.chat.completions.create(
        model="llama3-70b-8192",  
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=1.0,
        stream=True,
        stop=None
    )

    Answer = ""

    # concatenate response chunks from the streaming output
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content
    
    # clean up the response
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    # save the updated chat log back to the JSON file
    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    # remove the most recent system message from the chatbot conversation
    SystemChatBot.pop()
    return AnswerModifier(Answer = Answer) 

# main entry point for the program for interactive querrying
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealTimeSearchEngine(prompt))  # call the real-time search engine with the user's query
           
        

