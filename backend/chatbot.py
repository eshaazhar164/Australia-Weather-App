
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAMES = [
    "gemini-3.6-flash",
    "gemini-3.8-flash"
]

MAX_OUTPUT_TOKENS = 2000

SYSTEM_INSTRUCTION = """
You are an AI Weather Assistant for an Australia Weather Dashboard.

Your responsibilities:
1. Answer questions related to Australian weather.
2. Help users understand temperature, humidity, UV index and weather conditions.
3. Answer questions about Sydney, Melbourne, Brisbane, Perth,
   Adelaide, Canberra and Hobart.
4. Compare weather conditions between Australian cities.
5. Explain weather information in simple and clear language.
6. Stay focused on weather-related topics.
7. Use the live weather data provided in the user's message.
8. Never invent current weather values.
9. If live weather information is missing, clearly say so.
10. You can answer general weather education questions too.

RESPONSE STYLE:
1. Keep answers short, direct and to the point.
2. Answer exactly what the user asks. Do not add unrelated information.
3. Avoid long introductions and unnecessary explanations.
4. Do not repeat the same information in multiple sections.
5. Use headings and bullet points only when they improve readability.
6. For comparison questions, show the relevant values of all requested cities
   in a simple and organized list.
7. Clearly mention the highest and lowest values when relevant.
8. Add only one short concluding sentence if useful.
9. Do not add unnecessary safety advice or extra summaries.
10. Keep simple questions to 1-3 sentences.
11. For detailed questions, provide only the details needed to answer them.
12. Use proper Markdown formatting for headings, bold text and lists.
13. Never show unfinished headings or incomplete sentences.

IMPORTANT:
Be informative but concise. Do not make every answer unnecessarily long.
"""


def get_chatbot_response(message, weather_context="", history=None):

    if not API_KEY:
        return "Gemini API key is missing. Please check your .env file."

    client = None

    try:
        client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(
                timeout=30000,
                retry_options=types.HttpRetryOptions(
                    attempts=1
                )
            )
        )

        conversation = []

        if history:
            for item in history[-6:]:
                role = item.get("role")
                content = item.get("content", "")

                if role in ["user", "model"] and content:
                    conversation.append(
                        types.Content(
                            role=role,
                            parts=[types.Part(text=content)]
                        )
                    )

        current_message = f"""
Weather Information:
{weather_context}

User Question:
{message}
"""

        conversation.append(
            types.Content(
                role="user",
                parts=[types.Part(text=current_message)]
            )
        )

        for model_name in MODEL_NAMES:

            try:
                print(
                    f"Trying Gemini model: {model_name}",
                    flush=True
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=conversation,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.3,
                        max_output_tokens=MAX_OUTPUT_TOKENS
                    )
                )

                answer = response.text

                finish_reason = "Unknown"

                if response.candidates:
                    finish_reason = str(
                        response.candidates[0].finish_reason
                    )

                print(
                    f"Gemini finish reason: {finish_reason}",
                    flush=True
                )

                if answer:
                    print(
                        f"Gemini response length: {len(answer)} characters",
                        flush=True
                    )

                    print(
                        f"Gemini response: {answer}",
                        flush=True
                    )

                    return answer

                print(
                    f"Empty response from {model_name}",
                    flush=True
                )

            except Exception as error:
                print(
                    f"Gemini model {model_name} failed: {repr(error)}",
                    flush=True
                )

        return (
            "The AI service is temporarily busy. "
            "Please try again in a little while."
        )

    except Exception as error:
        print(
            f"Gemini API Error: {repr(error)}",
            flush=True
        )

        return (
            "Sorry, the chatbot is temporarily unavailable. "
            "Please try again."
        )

    finally:
        if client is not None:
            client.close()
