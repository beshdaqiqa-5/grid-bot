import os
import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Tokenni environment variable orqali o'rnat (Railway da BOT_TOKEN deb qo'sh)
TOKEN = os.environ.get("BOT_TOKEN", "")


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men rasm Grid Bot man.\n\n"
        "📸 Menga istalgan rasm yuboring — men uni grid qilib kesib qaytaraman.\n\n"
        "Masalan: 3x3 = 9 ta teng qism."
    )


# Rasm kelganda
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # eng yuqori sifatli versiyasi
    context.user_data["photo_file_id"] = photo.file_id

    keyboard = [
        [
            InlineKeyboardButton("2x2 (4 qism)", callback_data="2x2"),
            InlineKeyboardButton("3x3 (9 qism)", callback_data="3x3"),
        ],
        [
            InlineKeyboardButton("3x4 (12 qism)", callback_data="3x4"),
            InlineKeyboardButton("4x4 (16 qism)", callback_data="4x4"),
        ],
        [InlineKeyboardButton("✏️ O'zim kiritaman", callback_data="custom")],
    ]
    await update.message.reply_text(
        "Grid o'lchamini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# Tugma bosilganda
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "custom":
        context.user_data["waiting_custom"] = True
        await query.edit_message_text(
            "Grid o'lchamini yozing.\nFormat: qatorXustun\nMasalan: 3x3 yoki 2x4"
        )
        return

    rows, cols = map(int, query.data.split("x"))
    await query.edit_message_text(f"⏳ {rows}x{cols} grid tayyorlanmoqda...")
    await process_grid(query.message, context, rows, cols)


# Matn kelganda (custom o'lcham uchun)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_custom"):
        await update.message.reply_text("Rasm yuboring 📸")
        return

    text = update.message.text.strip().lower().replace(" ", "")
    try:
        parts = text.split("x")
        rows, cols = int(parts[0]), int(parts[1])
        if not (1 <= rows <= 10 and 1 <= cols <= 10):
            raise ValueError
    except Exception:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\nMasalan: 3x3 yoki 4x2 (1-10 oralig'ida)"
        )
        return

    context.user_data["waiting_custom"] = False
    await update.message.reply_text(f"⏳ {rows}x{cols} grid tayyorlanmoqda...")
    await process_grid(update.message, context, rows, cols)


# Rasmni kesib yuborish
async def process_grid(message, context: ContextTypes.DEFAULT_TYPE, rows: int, cols: int):
    file_id = context.user_data.get("photo_file_id")
    if not file_id:
        await message.reply_text("❌ Avval rasm yuboring!")
        return

    # Rasmni yuklab olish
    tg_file = await context.bot.get_file(file_id)
    file_bytes = await tg_file.download_as_bytearray()
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    width, height = img.size
    tile_w = width // cols
    tile_h = height // rows

    pieces = []
    for r in range(rows):
        for c in range(cols):
            left = c * tile_w
            top = r * tile_h
            right = min(left + tile_w, width)
            bottom = min(top + tile_h, height)

            tile = img.crop((left, top, right, bottom))
            buf = io.BytesIO()
            tile.save(buf, format="PNG")
            buf.seek(0)
            pieces.append(buf)

    # Telegram bir xabarda max 10 ta rasm qabul qiladi
    total = len(pieces)
    for batch_start in range(0, total, 10):
        batch = pieces[batch_start : batch_start + 10]
        media = [
            InputMediaPhoto(
                media=piece,
                caption=f"Qism {batch_start + i + 1}/{total}" if i == 0 else None,
            )
            for i, piece in enumerate(batch)
        ]
        await context.bot.send_media_group(chat_id=message.chat_id, media=media)

    await message.reply_text(f"✅ Tayyor! {total} ta qism yuborildi.")


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable o'rnatilmagan!")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
