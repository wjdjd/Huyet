import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp

# --- SOZLAMALAR ---
# Railway-ga yuklaganda o'zgartirmang. Tokenni Railway Variables-ga yozasiz.
BOT_TOKEN = os.getenv("8193306896:AAG1DmcCGfOcYyy57MZdOgOrEFC3NKQCR7c")

# Agar lokal kompyuterda test qilmoqchi bo'lsangiz, pastdagi izohni olib tashlang:
# BOT_TOKEN = "SIZNING_TOKENINGIZ_SHU_YERDA"

dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- ANIMATSIYA EMOGILARI ---
STATUS_EMOJIS = {
    "start": "🔍",
    "download": "⬇️",
    "upload": "📤",
    "done": "✅",
    "error": "❌"
}

async def download_video(url, message: types.Message):
    # 1. Jarayon boshlangani haqida xabar
    status_msg = await message.answer(f"{STATUS_EMOJIS['start']} Havola tekshirilmoqda...")
    
    # 2. Cookies faylni tekshirish
    cookie_file = 'cookies.txt'
    if not os.path.exists(cookie_file):
        cookie_file = None # Fayl yo'q bo'lsa, cookiesiz harakat qiladi

    # 3. Yuklash sozlamalari
    filename = f"downloads/{message.message_id}.mp4"
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_file, # Cookies shu yerda ishlatiladi
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        # Telegram Bot API cheklovi (50MB) tufayli juda katta fayllarni olmaymiz
        'max_filesize': 50 * 1024 * 1024 
    }

    try:
        # --- YUKLAB OLISH ---
        await status_msg.edit_text(f"{STATUS_EMOJIS['download']} Video serverga yuklanmoqda... \n\n⏳ Kuting...")
        
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            title = info.get('title', 'Video')
            # Haqiqiy fayl nomini aniqlash (ba'zida format o'zgarishi mumkin)
            if not os.path.exists(filename):
                filename = ydl.prepare_filename(info)

        # --- TELEGRAMGA YUBORISH ---
        await status_msg.edit_text(f"{STATUS_EMOJIS['upload']} Telegramga yuklanmoqda...")
        
        video_input = FSInputFile(filename)
        caption_text = f"🎥 <b>{title}</b>\n\n🤖 Bot orqali yuklandi."
        
        await message.answer_video(video=video_input, caption=caption_text, parse_mode="HTML")
        
        # --- TOZALASH ---
        await status_msg.delete()
        
    except yt_dlp.utils.DownloadError:
        await status_msg.edit_text(f"{STATUS_EMOJIS['error']} Videoni yuklab bo'lmadi.\nSabablar:\n1. Video yopiq (Private).\n2. Cookie fayl eskirgan.\n3. Hududiy cheklov.")
    except Exception as e:
        await status_msg.edit_text(f"{STATUS_EMOJIS['error']} Xatolik: {str(e)}")
    finally:
        # Nima bo'lgan taqdirda ham faylni serverdan o'chiramiz
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# --- LINKLARNI USHLASH ---
@dp.message(F.text.regexp(r'(https?://)?(www\.)?(instagram|tiktok|youtube|youtu)\.(com|be)/.*'))
async def link_handler(message: types.Message):
    # Downloads papkasini yaratish
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    await download_video(message.text, message)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Salom! Menga Instagram, TikTok yoki YouTube havolasini yuboring.")

# --- MAIN ---
async def main():
    if not BOT_TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi! Railway Variables bo'limini tekshiring.")
        return
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())