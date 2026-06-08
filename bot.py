import os
import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

TOKEN = os.environ.get("BOT_TOKEN", "")

SIZE_ADVICE = {
    "1x3":  ("1080x3240 px",  "1080x1080 px"),
    "1x4":  ("1080x4320 px",  "1080x1080 px"),
    "1x5":  ("1080x5400 px",  "1080x1080 px"),
    "1x6":  ("1080x6480 px",  "1080x1080 px"),
    "1x7":  ("1080x7560 px",  "1080x1080 px"),
    "1x8":  ("1080x8640 px",  "1080x1080 px"),
    "1x9":  ("1080x9720 px",  "1080x1080 px"),
    "1x10": ("1080x10800 px", "1080x1080 px"),
    "3x1":  ("3240x1080 px",  "1080x1080 px"),
    "3x2":  ("3240x2160 px",  "1080x1080 px"),
    "3x3":  ("3240x3240 px",  "1080x1080 px"),
}

WELCOME = (
    "Salom! Instagram Grid Bot\n\n"
    "Rasm yuboring -- foto yoki fayl sifatida\n\n"
    "Carousel: 1/3 dan 1/10 gacha\n"
    "Post grid: 3/1 - 3/2 - 3/3\n\n"
    "Sifat saqlanadi (PNG, siqilmagan)\n"
    "Notogri olcham bolsa -- markazdan kesiladi\n"
    "Rasm yoki fayl sifatida qaytariladi"
)

HELP = (
    "Yordam\n\n"
    "Carousel -- 1 ustun, N qator:\n"
    "  1/3 = 3 qismga, 1/10 = 10 qismga\n"
    "  Har bir qism alohida Instagram slayd boladi.\n\n"
    "Post Grid -- 3 ustun, N qator:\n"
    "  3/3 = 9 ta post, profilda tolik rasm korinadi.\n\n"
    "Olcham maslahati:\n"
    "  Carousel 1/N: 1080 x (1080*N) px\n"
    "  Post 3/N: 3240 x (1080*N) px\n\n"
    "Chiqish formati:\n"
    "  Rasm: tezroq, lekin Telegram siqadi\n"
    "  Fayl: PNG, siqilmagan, tolik sifat\n\n"
    "Rasm yuboring -- boshlaylik!"
)


def kb_type():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Carousel", callback_data="type_carousel"),
            InlineKeyboardButton("Post",     callback_data="type_post"),
        ],
        [
            InlineKeyboardButton("Yordam",         callback_data="help"),
            InlineKeyboardButton("Qayta boshlash", callback_data="restart"),
        ],
    ])


def kb_carousel():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1/3",  callback_data="fmt_1x3"),
            InlineKeyboardButton("1/4",  callback_data="fmt_1x4"),
            InlineKeyboardButton("1/5",  callback_data="fmt_1x5"),
        ],
        [
            InlineKeyboardButton("1/6",  callback_data="fmt_1x6"),
            InlineKeyboardButton("1/7",  callback_data="fmt_1x7"),
            InlineKeyboardButton("1/8",  callback_data="fmt_1x8"),
        ],
        [
            InlineKeyboardButton("1/9",  callback_data="fmt_1x9"),
            InlineKeyboardButton("1/10", callback_data="fmt_1x10"),
        ],
        [
            InlineKeyboardButton("Orqaga",         callback_data="back"),
            InlineKeyboardButton("Qayta boshlash", callback_data="restart"),
        ],
    ])


def kb_post():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("3/1", callback_data="fmt_3x1"),
            InlineKeyboardButton("3/2", callback_data="fmt_3x2"),
            InlineKeyboardButton("3/3", callback_data="fmt_3x3"),
        ],
        [
            InlineKeyboardButton("Orqaga",         callback_data="back"),
            InlineKeyboardButton("Qayta boshlash", callback_data="restart"),
        ],
    ])


def kb_output(key):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Rasm sifatida", callback_data="out_photo_" + key),
            InlineKeyboardButton("Fayl sifatida", callback_data="out_file_" + key),
        ],
        [
            InlineKeyboardButton("Orqaga",         callback_data="back"),
            InlineKeyboardButton("Qayta boshlash", callback_data="restart"),
        ],
    ])


def kb_done():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Xuddi shu rasm, boshqa format", callback_data="reuse_image")],
        [InlineKeyboardButton("Boshqa rasm yuborish",          callback_data="new_image")],
        [
            InlineKeyboardButton("Orqaga",         callback_data="back"),
            InlineKeyboardButton("Qayta boshlash", callback_data="restart"),
        ],
        [InlineKeyboardButton("Yordam", callback_data="help")],
    ])


def kb_reuse():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Carousel", callback_data="type_carousel"),
            InlineKeyboardButton("Post",     callback_data="type_post"),
        ],
        [
            InlineKeyboardButton("Boshqa rasm yuborish", callback_data="new_image"),
            InlineKeyboardButton("Qayta boshlash",       callback_data="restart"),
        ],
    ])


async def cmd_start(update, context):
    context.user_data.clear()
    await update.message.reply_text(WELCOME)


async def cmd_help(update, context):
    await update.message.reply_text(HELP)


async def handle_media(update, context):
    msg = update.message
    if msg.photo:
        context.user_data["file_id"] = msg.photo[-1].file_id
    elif msg.document:
        mime = msg.document.mime_type or ""
        if not mime.startswith("image/"):
            await msg.reply_text("Faqat rasm fayllari qabul qilinadi (PNG, JPG, WEBP...)")
            return
        context.user_data["file_id"] = msg.document.file_id
    else:
        return
    await msg.reply_text("Format turini tanlang:", reply_markup=kb_type())


async def handle_callback(update, context):
    q = update.callback_query
    await q.answer()
    d = q.data

    if d == "restart":
        context.user_data.clear()
        await q.edit_message_text(WELCOME)
        return

    if d == "help":
        await q.edit_message_text(HELP,
                                  reply_markup=InlineKeyboardMarkup([
                                      [
                                          InlineKeyboardButton("Orqaga",         callback_data="back_from_help"),
                                          InlineKeyboardButton("Qayta boshlash", callback_data="restart"),
                                      ]
                                  ]))
        return

    if d == "back_from_help":
        if context.user_data.get("file_id"):
            await q.edit_message_text("Format turini tanlang:", reply_markup=kb_type())
        else:
            await q.edit_message_text(WELCOME)
        return

    if d == "new_image":
        context.user_data.clear()
        await q.edit_message_text("Yangi rasm yuboring:")
        return

    if d == "reuse_image":
        if not context.user_data.get("file_id"):
            await q.edit_message_text("Rasm topilmadi. Qayta yuboring:")
            return
        await q.edit_message_text("Format turini tanlang:", reply_markup=kb_reuse())
        return

    if d == "back":
        await q.edit_message_text("Format turini tanlang:", reply_markup=kb_type())
        return

    if d == "type_carousel":
        await q.edit_message_text(
            "Carousel -- nechta qismga bolish?\n\n1/3 = 3 ta slayd, 1/10 = 10 ta slayd\nOptimal: 1080 x (1080 x N) px",
            reply_markup=kb_carousel(),
        )
        return

    if d == "type_post":
        await q.edit_message_text(
            "Post Grid -- olcham tanlang:\n\n3/3 = profilni toldiruvchi 9 ta post\nOptimal: 3240 x (1080 x N) px",
            reply_markup=kb_post(),
        )
        return

    if d.startswith("fmt_"):
        key = d[4:]
        cols, rows = map(int, key.split("x"))
        total_size, tile_size = SIZE_ADVICE.get(key, ("?", "?"))
        if not context.user_data.get("file_id"):
            await q.edit_message_text("Rasm topilmadi. Qayta yuboring.")
            return
        context.user_data["grid_key"] = key
        label = str(cols) + "/" + str(rows)
        await q.edit_message_text(
            label + " format tanlandi\n\nTavsiya: " + total_size + "\nHar bir qism: " + tile_size + "\n\nNatijani qanday yuborish kerak?",
            reply_markup=kb_output(key),
        )
        return

    if d.startswith("out_photo_") or d.startswith("out_file_"):
        as_photo = d.startswith("out_photo_")
        key = d[10:] if as_photo else d[9:]
        cols, rows = map(int, key.split("x"))
        if not context.user_data.get("file_id"):
            await q.edit_message_text("Rasm topilmadi. Qayta yuboring.")
            return
        mode = "rasm" if as_photo else "fayl"
        label = str(cols) + "/" + str(rows)
        await q.edit_message_text(label + " grid, " + mode + " sifatida tayyorlanmoqda...")
        await process_grid(q.message, context, cols, rows, key, as_photo=as_photo)


def smart_crop_center(img, cols, rows):
    target = cols / rows
    w, h = img.size
    ratio = w / h
    if abs(ratio - target) < 0.005:
        return img, False
    if ratio > target:
        nw = int(round(h * target))
        left = (w - nw) // 2
        return img.crop((left, 0, left + nw, h)), True
    else:
        nh = int(round(w / target))
        top = (h - nh) // 2
        return img.crop((0, top, w, top + nh)), True


async def process_grid(message, context, cols, rows, key, as_photo=False):
    tg_file = await context.bot.get_file(context.user_data["file_id"])
    raw = await tg_file.download_as_bytearray()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    orig_w, orig_h = img.size
    img, was_cropped = smart_crop_center(img, cols, rows)
    w, h = img.size
    tw = w // cols
    th = h // rows
    pieces = []
    for r in range(rows):
        for c in range(cols):
            l = c * tw
            t = r * th
            r2 = l + tw if c < cols - 1 else w
            b  = t + th if r < rows - 1 else h
            tile = img.crop((l, t, r2, b))
            buf = io.BytesIO()
            fmt = "JPEG" if as_photo else "PNG"
            save_kwargs = {"quality": 95, "subsampling": 0} if as_photo else {}
            tile.save(buf, format=fmt, **save_kwargs)
            buf.seek(0)
            ext = "jpg" if as_photo else "png"
            pieces.append((buf, key + "_part" + str(r * cols + c + 1).zfill(2) + "." + ext))
    total = len(pieces)
    crop_note = ("\nRasm kesildi: " + str(orig_w) + "x" + str(orig_h) + " -> " + str(w) + "x" + str(h) + " px") if was_cropped else ""
    mode_note = "rasm sifatida" if as_photo else "PNG fayl (siqilmagan)"
    label = str(cols) + "/" + str(rows)
    for i in range(0, total, 10):
        batch = pieces[i: i + 10]
        if as_photo:
            media = [
                InputMediaPhoto(
                    media=buf,
                    caption="Qism " + str(i + j + 1) + "/" + str(total) if j == 0 else None,
                )
                for j, (buf, _) in enumerate(batch)
            ]
        else:
            media = [
                InputMediaDocument(
                    media=buf,
                    filename=fname,
                    caption="Qism " + str(i + j + 1) + "/" + str(total) if j == 0 else None,
                )
                for j, (buf, fname) in enumerate(batch)
            ]
        await context.bot.send_media_group(chat_id=message.chat_id, media=media)
    await message.reply_text(
        "Tayyor! " + str(total) + " ta qism -- " + mode_note + " (" + str(tw) + "x" + str(th) + " px)" + crop_note + "\n\nKeyingi qadam:",
        reply_markup=kb_done(),
    )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN ornatilmagan!")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_media))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
