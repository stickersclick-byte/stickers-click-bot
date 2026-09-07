import logging
import sqlite3
import io
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from PIL import Image
from moviepy.editor import VideoFileClip

# ================= НАСТРОЙКИ БОТА =================
TOKEN = 8255516081:AAH5SQU_2qm3-b6f2dsC5S9xD260QBHa3X8  # Вставь сюда токен от @BotFather
BOT_USERNAME = @StickersClickBot  # Вставь юзернейм бота БЕЗ @
# ==================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("stickers_click.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lang TEXT DEFAULT "ru", premium INTEGER DEFAULT 0)')
conn.commit()

class StickerStates(StatesGroup):
    wait_for_photo = State()
    wait_for_video = State()

LOCALIZATION = {
    'ru': {
        'welcome': "👋 Приветствуем в **Stickers Click**! Я помогу тебе создать любые стикеры.\nВыбери действие в меню ниже:",
        'btn_create': "🎨 Создать Стикеры",
        'btn_lang': "🌐 Сменить язык / Change Language",
        'btn_tariff': "💎 Тарифы и Преимущества",
        'choose_type': "Какой тип стикеров ты хочешь создать?",
        'type_regular': "🖼️ Обычные (Из фото)",
        'type_animated': "🎬 Анимированные (Из видео)",
        'premium_alert': "⚠️ Создание видео-стикеров доступно только для пользователей с активной подпиской VIP Клик!",
        'tariffs': "📊 **Тарифные планы Stickers Click:**\n\n1️⃣ **Базовый** (Бесплатно): Обычные стикеры.\n2️⃣ **VIP Клик** (299 ₽ / мес): Создание крутых анимированных видео-стикеров без ограничений.",
        'buy_btn': "💳 Купить 'VIP Клик'",
        'lang_changed': "Язык успешно изменен на Русский!",
        'send_photo': "📸 Отправь мне **любую картинку**. Я сам изменю её размер под стандарты Telegram и добавлю в твой пак!",
        'send_video': "🎬 Отправь мне **любое короткое видео**. Я сам обрежу его до 3 секунд, сожму и сделаю анимированный стикер!",
        'success': "🎉 Стикер успешно добавлен в твой пак!\n👉 Ссылка на пак: t.me/addstickers/",
        'error': "❌ Ошибка обработки. Убедись, что файл корректный."
    },
    'en': {
        'welcome': "👋 Welcome to **Stickers Click**! I will help you create any stickers.\nChoose an action from the menu below:",
        'btn_create': "🎨 Create Stickers",
        'btn_lang': "🌐 Change Language / Сменить язык",
        'btn_tariff': "💎 Tariffs & Benefits",
        'choose_type': "What type of stickers do you want to create?",
        'type_regular': "🖼️ Regular (From photo)",
        'type_animated': "🎬 Animated (From video)",
        'premium_alert': "⚠️ Creating video stickers is only available for users with an active VIP Click subscription!",
        'tariffs': "📊 **Stickers Click Tariffs:**\n\n1️⃣ **Basic** (Free): Regular stickers.\n2️⃣ **VIP Click** ($3.99 / mo): Unlimited video-sticker creation from your files.",
        'buy_btn': "💳 Buy 'VIP Click'",
        'lang_changed': "Language successfully changed to English!",
        'send_photo': "📸 Send me **any image**. I will automatically resize it for Telegram and add it to your pack!",
        'send_video': "🎬 Send me **any short video**. I will crop it to 3 seconds, resize it, and make an animated sticker!",
        'success': "🎉 Sticker successfully added to your pack!\n👉 Pack link: t.me/addstickers/",
        'error': "❌ Processing error. Make sure the file is correct."
    }
}

def get_user_data(user_id):
    cursor.execute("SELECT lang, premium FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return 'ru', 0
    return row[0], row[1]

def main_menu_keyboard(lang):
    text = LOCALIZATION[lang]
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=text['btn_create']))
    builder.add(types.KeyboardButton(text=text['btn_tariff']))
    builder.add(types.KeyboardButton(text=text['btn_lang']))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def resize_sticker_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((512, 512))
    final_img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    final_img.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2))
    out_bytes = io.BytesIO()
    final_img.save(out_bytes, format="PNG")
    out_bytes.seek(0)
    return out_bytes.getvalue()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang, _ = get_user_data(message.from_user.id)
    await message.answer(LOCALIZATION[lang]['welcome'], reply_markup=main_menu_keyboard(lang), parse_mode="Markdown")

@dp.message(F.text.in_([LOCALIZATION['ru']['btn_lang'], LOCALIZATION['en']['btn_lang']]))
async def change_lang_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"))
    builder.add(types.InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"))
    await message.answer("Выберите язык / Select language:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[2]
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (new_lang, callback.from_user.id))
    conn.commit()
    await callback.answer()
    await callback.message.answer(LOCALIZATION[new_lang]['lang_changed'], reply_markup=main_menu_keyboard(new_lang))

@dp.message(F.text.in_([LOCALIZATION['ru']['btn_create'], LOCALIZATION['en']['btn_create']]))
async def create_stickers_menu(message: types.Message):
    lang, _ = get_user_data(message.from_user.id)
    text = LOCALIZATION[lang]
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=text['type_regular'], callback_data="go_regular"))
    builder.add(types.InlineKeyboardButton(text=text['type_animated'], callback_data="go_video"))
    builder.adjust(1)
    await message.answer(text['choose_type'], reply_markup=builder.as_markup())

@dp.callback_query(F.data == "go_regular")
async def start_regular(callback: types.CallbackQuery, state: FSMContext):
    lang, _ = get_user_data(callback.from_user.id)
    await state.set_state(StickerStates.wait_for_photo)
    await callback.message.answer(LOCALIZATION[lang]['send_photo'])
    await callback.answer()

@dp.callback_query(F.data == "go_video")
async def start_video(callback: types.CallbackQuery, state: FSMContext):
    lang, is_premium = get_user_data(callback.from_user.id)
    if not is_premium:
        await callback.answer(LOCALIZATION[lang]['premium_alert'], show_alert=True)
        return
    await state.set_state(StickerStates.wait_for_video)
    await callback.message.answer(LOCALIZATION[lang]['send_video'])
    await callback.answer()

@dp.message(StickerStates.wait_for_photo, F.photo)
async def process_photo_sticker(message: types.Message, state: FSMContext):
    lang, _ = get_user_data(message.from_user.id)
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        resized_png = resize_sticker_image(downloaded_file.read())
        pack_name = f"pack_{message.from_user.id}_by_{BOT_USERNAME}"
        sticker_file = types.BufferedInputFile(resized_png, filename="sticker.png")
        input_sticker = types.InputSticker(sticker=sticker_file, emoji_list=["🎨"])
        try:
            await bot.add_sticker_to_set(user_id=message.from_user.id, name=pack_name, sticker=input_sticker)
        except Exception:
            await bot.create_new_sticker_set(user_id=message.from_user.id, name=pack_name, title=f"Static Pack #{message.from_user.id}", stickers=[input_sticker], sticker_format="static")
        await message.answer(f"{LOCALIZATION[lang]['success']}{pack_name}")
        await state.clear()
    except Exception as e:
        logging.error(e)
        await message.answer(LOCALIZATION[lang]['error'])

@dp.message(StickerStates.wait_for_video, F.video | F.document)
async def process_video_sticker(message: types.Message, state: FSMContext):
    lang, _ = get_user_data(message.from_user.id)
    file_id = message.video.file_id if message.video else message.document.file_id
    input_path = f"input_{message.from_user.id}.mp4"
    output_path = f"output_{message.from_user.id}.webm"
    msg_wait = await message.answer("⏳ Обрабатываю видео, подождите...")
    try:
        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, destination=input_path)
        clip = VideoFileClip(input_path).subclip(0, min(3, VideoFileClip(input_path).duration))
        clip_resized = clip.resize(newsize=(512, 512))
        clip_resized.write_videofile(output_path, codec='libvpx-vp9', audio=False, bitrate="200k")
        clip.close()
        clip_resized.close()
        pack_name = f"video_{message.from_user.id}_by_{BOT_USERNAME}"
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
        sticker_file = types.BufferedInputFile(video_bytes, filename="sticker.webm")
        input_sticker = types.InputSticker(sticker=sticker_file, emoji_list=["🎬"])
        try:
            await bot.add_sticker_to_set(user_id=message.from_user.id, name=pack_name, sticker=input_sticker)
        except Exception:
            await bot.create_new_sticker_set(user_id=message.from_user.id, name=pack_name, title=f"Video Pack #{message.from_user.id}", stickers=[input_sticker], sticker_format="video")
        await msg_wait.delete()
        await message.answer(f"{LOCALIZATION[lang]['success']}{pack_name}")
