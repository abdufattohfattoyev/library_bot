import logging
from aiogram import executor
from loader import dp, bot
from utils.db_api.users import init_users_db
from utils.db_api.jurnallar import init_journals_db

# Handlerlarni import qilish
import handlers.users.start  # User handlerlar
import handlers.users.admin  # Admin handlerlar

# Logging ni sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def on_startup(dispatcher):
    """Bot ishga tushganda"""
    logger.info("Bot ishga tushmoqda...")

    # Ma'lumotlar bazasini yaratish (users va journals)
    try:
        init_users_db()
        init_journals_db()
        logger.info("Ma'lumotlar bazasi muvaffaqiyatli yaratildi")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasi yaratishda xatolik: {str(e)}")
        return

    # Bot ma'lumotlarini olish
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Bot ma'lumotlarini olishda xatolik: {str(e)}")

async def on_shutdown(dispatcher):
    """Bot to'xtaganda"""
    logger.info("Bot to'xtatilmoqda...")

    try:
        await dp.storage.close()
        await dp.storage.wait_closed()
        logger.info("Bot muvaffaqiyatli to'xtatildi")
    except Exception as e:
        logger.error(f"Bot to'xtatishda xatolik: {str(e)}")

if __name__ == '__main__':
    try:
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
    except Exception as e:
        logger.error(f"Bot ishga tushishda xatolik: {str(e)}")