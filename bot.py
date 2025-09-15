import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from video_utils import get_video_info, compress_video, convert_resolution

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Read from env var (set in Colab or .env)

RESOLUTIONS = {
    "144p": 144,
    "240p": 240,
    "360p": 360,
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
    "2K": 1440,
    "4K": 2160,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a video file (max 2GB) to convert or compress.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    if video.file_size > 2 * 1024 * 1024 * 1024:
        await update.message.reply_text("❌ File exceeds 2GB limit.")
        return

    file_id = video.file_id
    file = await context.bot.get_file(file_id)
    ext = os.path.splitext(video.file_name or "video.mp4")[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    await update.message.reply_text("⬇️ Downloading your video...")
    await file.download_to_drive(filepath)
    context.user_data["video_path"] = filepath

    info = get_video_info(filepath)
    if "error" in info:
        await update.message.reply_text("⚠️ Could not extract video info.")
        return

    msg = (
        f"🎬 *Video Info:*\n"
        f"📁 File: `{info['filename']}`\n"
        f"📐 Resolution: {info['width']}x{info['height']}\n"
        f"⏱ Duration: {info['duration']:.2f}s\n"
        f"💾 Size: {info['size_mb']} MB\n"
        f"🎞 Codec: {info['video_codec']} / {info['audio_codec']}\n"
        f"🔊 Bitrate: {info['bitrate']}\n"
    )
    await update.message.reply_markdown(msg)

    buttons = [
        [InlineKeyboardButton(res, callback_data=res)] for res in RESOLUTIONS
    ]
    buttons.append([InlineKeyboardButton("🗜 Compress (same resolution)", callback_data="compress")])
    await update.message.reply_text(
        "🔧 Choose conversion or compression option:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selection = query.data
    video_path = context.user_data.get("video_path")

    if not video_path or not os.path.exists(video_path):
        await query.edit_message_text("❌ Video file not found.")
        return

    filename = os.path.basename(video_path)
    output_path = os.path.join(DOWNLOAD_DIR, f"processed_{filename}")
    await query.edit_message_text("⏳ Processing...")

    try:
        if selection == "compress":
            compress_video(video_path, output_path)
        elif selection in RESOLUTIONS:
            convert_resolution(video_path, output_path, RESOLUTIONS[selection])
        else:
            await query.edit_message_text("❌ Invalid option.")
            return

        if os.path.getsize(output_path) > 2 * 1024 * 1024 * 1024:
            await query.message.reply_text("❌ Converted file is too large (>2GB) to upload.")
        else:
            from telegram import InputFile

if not os.path.exists(output_path):
    await query.message.reply_text("❌ Converted file not found.")
    return

if os.path.getsize(output_path) > 2 * 1024 * 1024 * 1024:
    await query.message.reply_text("❌ Converted file too large (>2GB) to send.")
    return

try:
    await query.message.reply_video(video=InputFile(output_path))
except Exception as e:
    await query.message.reply_text(f"❌ Upload error: {str(e)}")

    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def error_handler(update, context):
    print(f"[ERROR] {context.error}")

def main():
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in environment variables.")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
