import sys
import os

# Add the project's root directory to the Python path to resolve import errors
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import requests
import geocoder
import re
import datetime
from dotenv import dotenv_values
from groq import Groq
from ddgs.ddgs import DDGS
from Backend.Utils import resource_path

# --- Configuration ---
env_path = resource_path(".env")
if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at: {env_path}")

env_vars = dotenv_values(env_path)

GroqAPIKey = env_vars.get("GroqAPIKey")
WeatherAPIKey = env_vars.get("OpenWeatherMapAPIKey")
NewsAPIKey = env_vars.get("NewsAPIKey")
TMDB_KEY = env_vars.get("TMDBKey")
AlphaVantageKey = env_vars.get("AlphaVantageKey")


if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in .env file.")

client = Groq(api_key=GroqAPIKey)

# --- Tool Definitions ---

def get_weather(city: str) -> str:
    """Fetches the current weather for a specified city. If the city is not provided, it attempts to geolocate via IP address."""
    try:
        if not WeatherAPIKey:
            return "Error: OpenWeatherMap API key is not configured."
        
        if not city:
            g = geocoder.ip("me")
            if g.ok:
                city = g.city
            else:
                return "Could not determine your location. Please specify a city, like 'weather in London'."

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WeatherAPIKey}&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return f"Error: Could not retrieve weather for {city}. {data.get('message', '')}"

        description = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        return f"The current weather in {city} is {description} with a temperature of {temp}°C, which feels like {feels_like}°C."

    except Exception as e:
        return f"An error occurred while fetching weather: {e}"

def get_stock_price(symbol: str) -> str:
    """Fetches the latest stock price for a given stock symbol or company name."""
    try:
        if not AlphaVantageKey:
            return "Error: Alpha Vantage API key is not configured."

        # First, search for the best symbol match for the company name
        search_url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={symbol}&apikey={AlphaVantageKey}'
        r = requests.get(search_url)
        data = r.json()
        best_match = data.get('bestMatches', [])
        if not best_match:
            return f"Sorry, I couldn't find a stock symbol for '{symbol}'."
        
        stock_symbol = best_match[0]['1. symbol']
        company_name = best_match[0]['2. name']

        # Now get the quote for that symbol
        quote_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey={AlphaVantageKey}'
        r = requests.get(quote_url)
        data = r.json().get('Global Quote', {})

        if not data:
            return f"Sorry, I couldn't fetch the stock price for {company_name} ({stock_symbol})."

        price = data.get('05. price')
        change = data.get('10. change percent')
        return f"The current stock price for {company_name} ({stock_symbol}) is ${float(price):.2f}. The change today is {change}."

    except Exception as e:
        return f"An error occurred while fetching stock price: {e}"


def get_latest_news(topic: str = None) -> str:
    """Fetches top 5 news headlines. If a topic is provided, it searches for that topic. Otherwise, it returns general breaking news."""
    try:
        if not NewsAPIKey:
            return "Error: NewsAPI key is not configured."
        
        # If topic is generic, get general top headlines
        if topic and topic.lower() in ["news", "breaking news", "headlines"]:
            topic = None

        if topic:
            url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NewsAPIKey}&language=en&pageSize=5&sortBy=publishedAt"
        else:
            # Default to top headlines in India if no specific topic
            url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NewsAPIKey}&pageSize=5"

        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or data.get("status") != "ok":
            return f"Error: Could not retrieve news."

        articles = data.get("articles", [])
        if not articles:
            return f"No recent news found for the given query."
            
        headlines = "\n".join([f"- {article['title']}" for article in articles])
        search_term = f"about {topic}" if topic else "for today"
        return f"Here are the latest headlines {search_term}:\n{headlines}"
    
    except Exception as e:
        return f"An error occurred while fetching news: {e}"

def calculate_math(expression: str) -> str:
    """Calculates the result of a mathematical expression. Example: '2 + 2 * 10'."""
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return f"The result of {expression} is {result}."
    except Exception:
        return "Sorry, I couldn't calculate that. Please provide a valid mathematical expression."

def perform_web_search(query: str) -> str:
    """Performs a comprehensive web search when no other specific tool is suitable. Gathers information and synthesizes a detailed answer."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        
        if not results:
            return f"Sorry, I couldn't find any information on '{query}'."

        context = "\n\n".join([f"Source {i+1}: {res['body']}" for i, res in enumerate(results)])
        
        synthesis_prompt = f"""
        Based on the following information, provide a clear and comprehensive answer to the user's query.
        User Query: "{query}"
        Search Results Context:\n---\n{context}\n---\nSynthesized Answer:
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.7,
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"An error occurred during web search: {e}"

# --- Tool Definitions for the Agent ---
tools = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
    "get_latest_news": get_latest_news,
    "calculate_math": calculate_math,
    "perform_web_search": perform_web_search,
}

tool_descriptions = """
You have access to the following tools:
1. get_weather(city: str): Fetches current weather. Use for questions about weather or temperature.
2. get_stock_price(symbol: str): Fetches the latest stock price for a company name or stock symbol.
3. get_latest_news(topic: str): Gets latest news headlines. Use for questions about current events or news. If the user asks for general news, call it without a topic.
4. calculate_math(expression: str): Solves a mathematical expression.
5. perform_web_search(query: str): Default tool for complex questions or any query not fitting other tools.
"""

# --- Main Agent Logic ---
def RealTimeSearchEngine(prompt: str):
    """
    An advanced real-time search engine that uses an AI agent to select the best tool for a given query.
    """
    system_prompt = f"""
    You are an intelligent routing agent. Your task is to analyze the user's query and decide which tool is most appropriate.
    {tool_descriptions}
    Respond ONLY with a single JSON object with 'tool_name' and 'arguments'. 'arguments' MUST be a JSON object (a dictionary).
    Example: For the query "weather in Boston", you should respond with:
    {{"tool_name": "get_weather", "arguments": {{"city": "Boston"}}}}
    The current date is {datetime.datetime.now().strftime('%Y-%m-%d')}.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        
        response_text = completion.choices[0].message.content
        tool_call = json.loads(response_text)
        
        tool_name = tool_call.get("tool_name")
        arguments = tool_call.get("arguments", {})

        if tool_name in tools:
            tool_function = tools[tool_name]
            
            # Robust argument handling
            if not isinstance(arguments, dict):
                 import inspect
                 sig = inspect.signature(tool_function)
                 param_name = next(iter(sig.parameters))
                 arguments = {param_name: arguments}

            result = tool_function(**arguments)
            return result
        else:
            return perform_web_search(prompt)

    except Exception as e:
        print(f"[RealTimeSearchEngine Error] - {e}. Defaulting to web search.")
        return perform_web_search(prompt)

# --- Interactive Mode for Testing ---
if __name__ == "__main__":
    while True:
        user_prompt = input("Enter your query: ")
        if user_prompt.lower() in ["exit", "quit"]:
            break
        answer = RealTimeSearchEngine(user_prompt)
        print(f"\nNovus: {answer}\n")

