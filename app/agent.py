# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.genai import types

from app.firestore_tools import (
    export_recipe_to_gcs,
    fetch_online_recipes,
    generate_recipe_image,
    get_all_recipes,
    get_favorite_recipes,
    save_recipe,
    search_recipes,
    toggle_favorite_recipe,
)


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


DEPLOYMENT_METADATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deployment_metadata.json"
)


def _get_agent_engine_resource_name() -> str:
    if os.path.exists(DEPLOYMENT_METADATA_PATH):
        try:
            with open(DEPLOYMENT_METADATA_PATH, "r") as f:
                data = json.load(f)
                res_id = data.get("remote_agent_runtime_id")
                if res_id:
                    return res_id
        except Exception:
            pass
    return "projects/358830685831/locations/us-east4/reasoningEngines/6314965869294256128"


code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=_get_agent_engine_resource_name()
)


from google.adk.agents import Context
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.tools.load_memory_tool import load_memory_tool
from google.adk.tools.preload_memory_tool import preload_memory_tool
from google.adk.tools.tool_context import ToolContext


async def save_user_memory(fact: str, tool_context: ToolContext) -> str:
    """Saves a new user allergy, dietary restriction, or preference directly into long-term memory bank on GCP.

    Args:
        fact: The specific user allergy, restriction, or preference to save (e.g. 'User is allergic to shellfish').
    """
    entry = MemoryEntry(content=types.Content(parts=[types.Part.from_text(text=fact)], role="user"))
    await tool_context.add_memory(memories=[entry])
    return f"Successfully saved to Vertex AI Memory Bank: {fact}"


async def auto_save_memory_callback(ctx: Context):
    try:
        await ctx.add_session_to_memory()
    except Exception as e:
        import logging
        logging.warning("Failed to auto-save session to memory bank: %s", e)


instruction = (
    "You are a friendly and expert Recipe Assistant. "
    "You help users discover recipes based on ingredients they have on hand, "
    "manage their favorite recipes, and save new recipes to their Firestore database.\n\n"
    "Always remember and respect all user allergies, dietary restrictions, and preferences across all conversations.\n"
    "- When the user tells you about a new allergy, dietary restriction, or preference, call the `save_user_memory` tool to save it immediately to GCP Memory Bank.\n"
    "- When asked about past conversations, user allergies, dietary restrictions, or preferences, ALWAYS call the `load_memory` tool with a relevant query (e.g. 'allergies') to look up their saved memories from the memory bank before answering.\n\n"
    "When performing calculations, data analysis, or running Python code, write the Python code inside ```python ... ``` code blocks so it can be executed."
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    after_agent_callback=auto_save_memory_callback,
    tools=[
        preload_memory_tool,
        load_memory_tool,
        save_user_memory,
        generate_recipe_image,
        fetch_online_recipes,
        export_recipe_to_gcs,
        get_all_recipes,
        search_recipes,
        get_favorite_recipes,
        save_recipe,
        toggle_favorite_recipe,
        get_weather,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
