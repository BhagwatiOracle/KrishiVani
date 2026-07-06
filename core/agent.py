from groq import Groq
from dotenv import load_dotenv
from gtts import gTTS
from langdetect import detect
import os

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_language(text: str) -> str:
    """Returns 'hi' for Hindi, 'en' for English, else 'hi' as default."""
    try:
        lang = detect(text)
        return lang if lang in ["hi", "en"] else "hi"
    except Exception:
        return "hi"
    

def _build_messages(system_prompt: str, history: list[dict] | None, user_content: str) -> list[dict]:
    """Assemble a messages list: system + prior turns + new user turn."""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        # history rows look like {"role": "user"/"assistant", "content": "..."}
        messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    return messages
    
#---------------------------------------------------------------------------    

SYSTEM_PROMPT = """You are KisanVoice, an expert agricultural advisor for Indian farmers.
You have deep knowledge of crop diseases, organic and chemical treatments, 
Indian farming practices, seeds, fertilizers, weather, and market prices.

Rules:
- If the question is in Hindi → reply ONLY in Hindi (Devanagari script)
- If the question is in English → reply ONLY in English
- Maximum 120 words — this is a WhatsApp message
- Simple language, no technical jargon
- Mention cost in Indian Rupees whenever relevant
- Suggest  actions the farmer must take to treat/prevent the disease.
- End with ONE prevention tip
- Never mix Hindi and English in the same reply"""


def get_advice(disease_label: str, confidence: float, transcript: str ="", reply_language: str = "en",history:list[dict] | None = None)-> str:

    """Get advice from Groq based on the disease label, confidence, and farmer's question."""

    USER_PROMPT = f"""A farmer has a crop disease with {confidence:.2f}% confidence of being {disease_label}.
    The farmer's question is: "{transcript}".
    Write an advisory message in {reply_language} following format:
    Disease name with its prevention and treatment tips."""

    messages = _build_messages(SYSTEM_PROMPT, history=history, user_content=USER_PROMPT)

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",   # Fast + free on Groq
        messages=messages,
        max_tokens=200,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


def answer_general_question(user_text: str, language_code: str = "en", history: list[dict] | None = None)-> str:
    """Answer any farming question — not necessarily disease related."""

    lang_instruction = "reply in Hindi" if language_code == "hi" else "reply in English"
    user_prompt = f"{lang_instruction}. The farmer's question is: {user_text}"

    messages = _build_messages(SYSTEM_PROMPT, history=history, user_content=user_prompt)

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages= messages,
        max_tokens=200,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()




