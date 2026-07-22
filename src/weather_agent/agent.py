#!/usr/bin/env python3
"""
agent.py

Weather Agent implementation for Vertex AI Reasoning Engine / ADK.
Uses Gemini with tool calling (get_current_weather) to answer weather queries.
"""

from typing import Dict, Any, Optional
import vertexai
from vertexai.generative_models import GenerativeModel


def get_current_weather(location: str) -> str:
    """Gets current weather conditions for a given location.
    
    Args:
        location: City and state/country, e.g. 'Seattle, WA' or 'Tokyo'
    """
    loc_lower = location.lower()
    if "seattle" in loc_lower:
        return "Seattle, WA: 65°F, Partly Cloudy, Humidity 55%, Wind 8mph NW."
    elif "tokyo" in loc_lower:
        return "Tokyo, Japan: 22°C (72°F), Clear Skies, Humidity 40%, Wind 5km/h E."
    elif "new york" in loc_lower or "nyc" in loc_lower:
        return "New York, NY: 58°F, Rain, Humidity 85%, Wind 12mph S."
    elif "london" in loc_lower:
        return "London, UK: 15°C (59°F), Overcast, Humidity 70%, Wind 10km/h W."
    else:
        return f"{location}: 70°F (21°C), Mostly Sunny, Humidity 50%, Wind 5mph."


class WeatherAgent:
    """Reasoning Engine Agent wrapping Gemini model with weather tool capabilities."""
    
    def __init__(self, model_name: str = "gemini-1.5-flash-002"):
        self.model_name = model_name
        self.model = None

    def set_up(self):
        """Initializes model and registers weather tools."""
        self.model = GenerativeModel(
            model_name=self.model_name,
            tools=[get_current_weather],
            system_instruction="You are a helpful weather assistant. Use the get_current_weather tool to answer weather questions concisely."
        )

    def query(self, input: str, **kwargs) -> str:
        """Processes a weather query input prompt and returns response string."""
        if self.model is None:
            self.set_up()
            
        chat = self.model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(input)
        return response.text
