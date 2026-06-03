from pathlib import Path
import sys

# Add project root so `core` can be imported when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import detect_language, answer_general_question, text_to_audio, transcribe_audio


# Test 1 — Hindi text
text = "मेरे टमाटर की पत्तियां पीली हो रही हैं, क्या करूं?"
lang = detect_language(text)
reply1 = answer_general_question(text, lang)
print(f"Hindi reply:\n{reply1}\n")

# Test 2 — English text  
text = "My wheat crop has brown spots on the leaves. What should I do?"
lang = detect_language(text)
reply = answer_general_question(text, lang)
print(f"English reply:\n{reply}\n")

# Test 3 — Text to audio
audio_path = text_to_audio(reply1, lang_code="hi")
print(f"Audio saved to: {audio_path}")

# Test 4 — Transcribe a local audio file (if you have one)
# transcript, lang = transcribe_audio("my_voice_note.ogg")
# print(f"Transcript: {transcript} | Language: {lang}")