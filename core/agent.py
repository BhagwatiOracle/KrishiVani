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


def get_advice(disease_label: str, confidence: float, transcript: str ="", reply_language: str = "en")-> str:

    """Get advice from Groq based on the disease label, confidence, and farmer's question."""

    USER_PROMPT = f"""A farmer has a crop disease with {confidence:.2f}% confidence of being {disease_label}.
    The farmer's question is: "{transcript}".
    Write a WhatsApp advisory message in {reply_language} following format:
    Disease name with its prevention and treatment tips."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",   # Fast + free on Groq
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        max_tokens=200,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


def answer_general_question(user_text: str, language_code: str = "en")-> str:
    """Answer any farming question — not necessarily disease related."""
    lang_instruction = "reply in Hindi" if language_code == "hi" else "reply in English"

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{lang_instruction}. The farmer's question is: {user_text}"}
        ],
        max_tokens=200,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()




