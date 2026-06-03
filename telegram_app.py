import os
import tempfile
import base64
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.agent import *
from core.audio import *
from core.model import *

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("uploads", exist_ok=True)  # Ensure uploads directory exists

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

#-------------------Welcome Message--------------------------------

def  get_welcome_message(lang_code: str)-> str:
    if lang_code == "hi":
        return (
            "नमस्ते! 🌱 मैं KrishiVani हूँ, आपका कृषि सहायक।\n\n"
            "आप यह कर सकते हैं:\n"
            "• फसल की फोटो भेजें → बीमारी पहचान\n"
            "• आवाज़ में सवाल पूछें → आवाज़ में जवाब\n"
            "• हिंदी या English में लिखें\n\n"
            "अपनी फसल की समस्या बताइए!"
        )
    return (
        "Hello! 🌱 I am KrishiVani, your agriculture helper.\n\n"
        "You can:\n"
        "• Send a crop photo → get disease diagnosis\n"
        "• Send a voice note → get voice reply\n"
        "• Ask in Hindi or English\n\n"
        "Tell me about your crop problem!"
    )

def is_greeting(text: str)-> bool:
    greetings = {
        "hi", "hello", "hey", "helo", "start",
        "नमस्ते", "नमस्कार", "हेलो", "हाय",
        "sat sri akal", "good morning", "good evening"
    }
    return text.lower().strip() in greetings


#----------------------Telegram Bot Handlers------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handler."""
    await update.message.reply_text(get_welcome_message("en"))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user_text = update.message.text.strip()
    lang_code = detect_language(user_text)

    logger.info(f"Text: '{user_text}' | Lang: {lang_code}")

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    if is_greeting(user_text):
        reply = get_welcome_message(lang_code)
    else:
        reply = answer_general_question(user_text, language_code=lang_code)

    await update.message.reply_text(reply)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crop photos — run disease detection."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    logger.info("Image received, running disease detection...")

    # Download image from Telegram
    photo   = update.message.photo[-1]   # get highest resolution
    file    = await context.bot.get_file(photo.file_id)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".jpg", dir="uploads"
    )
    await file.download_to_drive(tmp.name)
    tmp.close()

    # Run disease detection
    predictions = predict_disease(tmp.name)
    top         = predictions[0]
    cleanup_audio_files(tmp.name)

    logger.info(f"Detected: {top['disease']} ({top['confidence']:.0%})")

    # Get language from caption if provided
    caption   = update.message.caption or ""
    lang_code = detect_language(caption) if caption else "en"

    reply = get_advice(
        disease_label  = top["disease"],
        confidence     = top["confidence"],
        transcript     = caption,
        reply_language = lang_code
    )
    

    await update.message.reply_text(reply)


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice notes — transcribe and reply with voice."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="record_voice"
    )

    logger.info("Voice note received...")

    # Get voice note file
    voice = update.message.voice or update.message.audio
    file  = await context.bot.get_file(voice.file_id)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".ogg", dir="uploads"
    )
    await file.download_to_drive(tmp.name)
    tmp.close()

    # Validate
    is_valid, error_msg = validate_audio(tmp.name)
    if not is_valid:
        cleanup_audio_files(tmp.name)
        await update.message.reply_text(f"Voice note error: {error_msg}")
        return

    # Transcribe
    transcript, lang_code = transcribe_audio(tmp.name)
    cleanup_audio_files(tmp.name)

    logger.info(f"Transcript: '{transcript}' | Lang: {lang_code}")

    if not transcript.strip():
        await update.message.reply_text(get_welcome_message(lang_code))
        return

    # Generate text reply
    reply_text = answer_general_question(transcript, language_code=lang_code)

    # Convert to voice
    audio_path = text_to_audio(reply_text, lang_code)

    # Send voice reply
    with open(audio_path, "rb") as audio_file:
        await update.message.reply_voice(voice=audio_file)

    # Also send text version
    await update.message.reply_text(reply_text)

    cleanup_audio_files(audio_path)


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stickers, documents, locations etc."""
    await update.message.reply_text(
        "कृपया फोटो, आवाज़ या टेक्स्ट भेजें। 🌱\n"
        "Please send a photo, voice note, or text.")
    


#----------------------Main Function------------------------------
def main():
    print("🚀 Starting KrishiVani Telegram bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO,   handle_image))
    app.add_handler(MessageHandler(filters.VOICE,   handle_audio))
    app.add_handler(MessageHandler(filters.AUDIO,   handle_audio))
    app.add_handler(MessageHandler(filters.ALL,     handle_unsupported))

    print("✅ KrishiVani bot is running! Open Telegram and message your bot.")
    print("Press Ctrl+C to stop.\n")

    # Start polling — no webhook, no ngrok needed
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()