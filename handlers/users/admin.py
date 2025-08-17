import os
import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from loader import dp, bot
from utils.db_api.jurnallar import (
    get_statistics, get_fanlar, get_bolimlar,
    add_jurnal, update_jurnal, delete_jurnal, get_jurnal_by_id,
    get_jurnallar
)
import logging
import asyncio

# Admin ID larini env fayldan olish
ADMINS = list(map(int, os.getenv("ADMINS", "").split(","))) if os.getenv("ADMINS") else []


class AddJurnalStates(StatesGroup):
    waiting_for_fan = State()
    waiting_for_bolim = State()
    waiting_for_name = State()
    waiting_for_image = State()
    waiting_for_frequency = State()
    waiting_for_website = State()
    waiting_for_contact = State()
    waiting_for_requirements = State()


class EditJurnalStates(StatesGroup):
    waiting_for_field = State()
    waiting_for_new_value = State()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMINS


def validate_url(url: str) -> bool:
    """URL ni tekshirish funksiyasi"""
    if not url or url.strip() == "":
        return True  # Bo'sh URL ham qabul qilinadi

    # URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// yoki https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP address
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return bool(url_pattern.match(url.strip()))

# Admin panel asosiy menyu
@dp.message_handler(commands=['admin'], state="*")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.finish()

    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return

    stats = get_statistics()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
    )
    keyboard.add(
        InlineKeyboardButton("➕ Jurnal qo'shish", callback_data="admin_add_jurnal"),
        InlineKeyboardButton("✏️ Jurnal tahrirlash", callback_data="admin_edit_jurnal")
    )
    keyboard.add(
        InlineKeyboardButton("🗑️ Jurnal o'chirish", callback_data="admin_delete_jurnal")
    )

    # Xavfsiz tarzda users_count ni olish
    users_count = stats.get('users_count', 0)

    text = f"""
🔧 **ADMIN PANEL**

📊 **Tezkor statistika:**
👥 Foydalanuvchilar: {users_count}
📚 Jurnallar: {stats['jurnallar_count']}
🎓 Fanlar: {stats['fanlar_count']}
🏛️ Bo'limlar: {stats['bolimlar_count']}

Kerakli amalni tanlang:
"""

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


# Statistika
@dp.callback_query_handler(lambda c: c.data == "admin_stats", state="*")
async def show_statistics(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not is_admin(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ Ruxsat yo'q!", show_alert=True)
        return

    try:
        stats = get_statistics()

        text = f"""
📊 **BATAFSIL STATISTIKA**

👥 **Foydalanuvchilar:** {stats['users_count']}
📚 **Jurnallar:** {stats['jurnallar_count']}
🎓 **Fanlar:** {stats['fanlar_count']}
🏛️ **Bo'limlar:** {stats['bolimlar_count']}

🏆 **Eng ko'p jurnali bo'lgan fan:**
{stats['top_fan']['nomi']} ({stats['top_fan']['jurnallar_soni']} ta jurnal)
"""

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_admin"))

        await bot.edit_message_text(
            text=text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"Statistikani ko'rsatishda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


# ================ JURNAL QO'SHISH ================

@dp.callback_query_handler(lambda c: c.data == "admin_add_jurnal", state="*")
async def start_add_jurnal(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not is_admin(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ Ruxsat yo'q!", show_alert=True)
        return

    try:
        fanlar = get_fanlar()

        keyboard = InlineKeyboardMarkup(row_width=1)
        for fan in fanlar:
            fan_nomi = fan['nomi']
            emoji_map = {
                "Fizika-matematika fanlari": "🔬",
                "Kimyo fanlari": "⚗️",
                "Biologiya fanlari": "🧬",
                "Geologiya-mineralogiya fanlari": "⛰️",
                "Texnika fanlari": "⚙️",
                "Qishloq xo'jaligi fanlari": "🌾",
                "Tarix fanlari": "📜",
                "Iqtisodiyot fanlari": "💰",
                "Falsafa fanlari": "🤔",
                "Filologiya fanlari": "📚",
                "Geografiya fanlari": "🌍",
                "Yuridik fanlar": "⚖️",
                "Pedagogika fanlari": "👨‍🏫",
                "Tibbiyot fanlari": "🏥",
                "Farmatsevtika fanlari": "💊",
                "Veterinariya fanlari": "🐕‍🦺",
                "San'atshunoslik fanlari": "🎨",
                "Arxitektura": "🏗️",
                "Psixologiya fanlari": "🧠",
                "Harbiy fanlar": "🎖️",
                "Sotsiologiya fanlari": "👥",
                "Siyosiy fanlar": "🗳️",
                "Islomshunoslik fanlari": "☪️"
            }
            emoji = emoji_map.get(fan_nomi, "📖")
            if len(fan_nomi) > 25:
                fan_nomi = fan_nomi[:22] + "..."

            keyboard.add(InlineKeyboardButton(f"{emoji} {fan_nomi}", callback_data=f"add_select_fan_{fan['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_admin"))

        await bot.edit_message_text(
            text="➕ **YANGI JURNAL QO'SHISH**\n\nFanni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        await AddJurnalStates.waiting_for_fan.set()
    except Exception as e:
        logging.error(f"Jurnal qo'shishni boshlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('add_select_fan_'), state=AddJurnalStates.waiting_for_fan)
async def add_select_bolim(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        fan_id = int(callback_query.data.split('_')[3])
        await state.update_data(fan_id=fan_id)

        bolimlar = get_bolimlar()

        keyboard = InlineKeyboardMarkup(row_width=1)
        for bolim in bolimlar:
            bolim_nomi = bolim['nomi']
            emoji_map = {
                "Milliy nashrlar": "🇺🇿",
                "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari": "🤝",
                "Evropa mamlakatlari nashrlari": "🇪🇺",
                "Amerika mamlakatlari nashrlari": "🌎"
            }
            emoji = emoji_map.get(bolim_nomi, "📄")

            if bolim_nomi == "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari":
                display_name = "🤝 MDH nashrlari"
            elif len(bolim_nomi) > 25:
                display_name = f"{emoji} {bolim_nomi[:22]}..."
            else:
                display_name = f"{emoji} {bolim_nomi}"

            keyboard.add(InlineKeyboardButton(display_name, callback_data=f"add_select_bolim_{bolim['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="admin_add_jurnal"))

        await bot.edit_message_text(
            text="🏛️ Bo'limni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )

        await AddJurnalStates.waiting_for_bolim.set()
    except Exception as e:
        logging.error(f"Bo'lim tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('add_select_bolim_'), state=AddJurnalStates.waiting_for_bolim)
async def ask_jurnal_name(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        bolim_id = int(callback_query.data.split('_')[3])
        await state.update_data(bolim_id=bolim_id)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="admin_add_jurnal"))

        await bot.edit_message_text(
            text="""📝 **Jurnal nomini kiriting:**

📋 **Misol:**
• Fizika va matematika jurnali
• O'zbekiston tibbiyot jurnali
• Qishloq xo'jaligi fanlari
• Tarixiy tadqiqotlar

*Jurnal nomini aniq va tushunarli yozing*""",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        await AddJurnalStates.waiting_for_name.set()
    except Exception as e:
        logging.error(f"Jurnal nomi so'rashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.message_handler(state=AddJurnalStates.waiting_for_name)
async def get_jurnal_name(message: types.Message, state: FSMContext):
    try:
        jurnal_name = message.text.strip()

        # Jurnal nomini tekshirish
        if len(jurnal_name) < 3:
            await message.answer("❌ Jurnal nomi kamida 3 ta belgidan iborat bo'lishi kerak!")
            return

        if len(jurnal_name) > 200:
            await message.answer("❌ Jurnal nomi 200 ta belgidan oshmasligi kerak!")
            return

        await state.update_data(nomi=jurnal_name)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_image"))

        await message.answer(
            "🖼️ Jurnal rasmini yuboring (yoki o'tkazib yuboring):",
            reply_markup=keyboard
        )

        await AddJurnalStates.waiting_for_image.set()
    except Exception as e:
        logging.error(f"Jurnal nomini olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


@dp.callback_query_handler(lambda c: c.data == "skip_image", state=AddJurnalStates.waiting_for_image)
@dp.message_handler(content_types=['photo'], state=AddJurnalStates.waiting_for_image)
async def get_image_or_skip(message_or_callback, state: FSMContext):
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            await state.update_data(rasmi=None)
            message = message_or_callback.message
        else:
            photo = message_or_callback.photo[-1]
            file_id = photo.file_id
            await state.update_data(rasmi=file_id)
            message = message_or_callback

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_frequency"))

        await message.answer(
            """📅 **Nashr chastotasini kiriting:**

📋 **Misollar:**
• Oyda bir marta
• Yilda 4 marta
• Har 3 oyda bir marta
• Yilda ikki marta
• Har oyda

*yoki o'tkazib yuboring*""",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        await AddJurnalStates.waiting_for_frequency.set()
    except Exception as e:
        logging.error(f"Rasm olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


@dp.callback_query_handler(lambda c: c.data == "skip_frequency", state=AddJurnalStates.waiting_for_frequency)
@dp.message_handler(state=AddJurnalStates.waiting_for_frequency)
async def get_frequency(message_or_callback, state: FSMContext):
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            frequency = None
            message = message_or_callback.message
        else:
            frequency = message_or_callback.text.strip()
            message = message_or_callback

        await state.update_data(nashr_chastotasi=frequency)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_website"))

        await message.answer(
            """🌐 **Jurnal saytini kiriting (URL):**

📋 **To'g'ri misollar:**
• https://journal.uz
• https://www.sciencejournal.uz
• http://academy.gov.uz/journal
• https://medical-journal.com

❌ **Noto'g'ri misollar:**
• journal.uz (https:// yo'q)
• www.jurnal.uz (https:// yo'q)
• jurnal sayti

*URL ni to'liq kiriting yoki o'tkazib yuboring*""",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        await AddJurnalStates.waiting_for_website.set()
    except Exception as e:
        logging.error(f"Chastotani olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


@dp.callback_query_handler(lambda c: c.data == "skip_website", state=AddJurnalStates.waiting_for_website)
@dp.message_handler(state=AddJurnalStates.waiting_for_website)
async def get_website(message_or_callback, state: FSMContext):
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            website = None
            message = message_or_callback.message
        else:
            website = message_or_callback.text.strip()
            # URL validatsiyasi
            if website and not validate_url(website):
                await message_or_callback.answer(
                    "❌ <b>Noto'g'ri URL format!</b>\n\n"
                    "✅ <b>To'g'ri misollar:</b>\n"
                    "• https://journal.uz\n"
                    "• https://www.example.com\n"
                    "• http://site.org\n\n"
                    "URL ni https:// yoki http:// bilan boshlang!",
                    parse_mode=ParseMode.HTML
                )
                return  # Bu yerda return bo'lishi kerak
            message = message_or_callback

        await state.update_data(jurnal_sayti=website)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_contact"))

        await message.answer(
            "📧 <b>Murojaat havolasini kiriting:</b>\n\n"
            "📋 <b>To'g'ri misollar:</b>\n"
            "• https://journal.uz/contact\n"
            "• mailto:editor@journal.uz\n"
            "• https://forms.google.com/contact\n"
            "• https://t.me/journal_admin\n\n"
            "❌ <b>Noto'g'ri misollar:</b>\n"
            "• journal.uz/contact (https:// yo'q)\n"
            "• editor@journal.uz (mailto: yo'q email uchun)\n\n"
            "<i>URL yoki email ni to'liq kiriting yoki o'tkazib yuboring</i>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

        await AddJurnalStates.waiting_for_contact.set()
    except Exception as e:
        logging.error(f"Saytni olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


@dp.callback_query_handler(lambda c: c.data == "skip_contact", state=AddJurnalStates.waiting_for_contact)
@dp.message_handler(state=AddJurnalStates.waiting_for_contact)
async def get_contact(message_or_callback, state: FSMContext):
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            contact = None
            message = message_or_callback.message
        else:
            contact = message_or_callback.text.strip()
            # URL yoki email validatsiyasi
            if contact:
                # Email tekshirish
                email_pattern = r'^mailto:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                # URL tekshirish
                if not (validate_url(contact) or re.match(email_pattern, contact)):
                    await message_or_callback.answer(
                        "❌ <b>Noto'g'ri format!</b>\n\n"
                        "✅ <b>To'g'ri misollar:</b>\n"
                        "• https://journal.uz/contact\n"
                        "• mailto:editor@journal.uz\n"
                        "• https://t.me/journal_admin\n\n"
                        "URL ni https:// bilan yoki email ni mailto: bilan boshlang!",
                        parse_mode=ParseMode.HTML
                    )
                    return  # Bu yerda return bo'lishi kerak
            message = message_or_callback

        await state.update_data(murojaat_link=contact)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_requirements"))

        await message.answer(
            "📋 <b>Jurnal talablari havolasini kiriting:</b>\n\n"
            "📋 <b>To'g'ri misollar:</b>\n"
            "• https://journal.uz/requirements\n"
            "• https://journal.uz/submission-guidelines\n"
            "• https://docs.google.com/document/requirements\n"
            "• https://journal.uz/authors-guide\n\n"
            "❌ <b>Noto'g'ri misollar:</b>\n"
            "• journal.uz/requirements (https:// yo'q)\n"
            "• talablar haqida\n\n"
            "<i>Talablar sahifasining to'liq URL ini kiriting yoki o'tkazib yuboring</i>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

        await AddJurnalStates.waiting_for_requirements.set()
    except Exception as e:
        logging.error(f"Kontaktni olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


@dp.callback_query_handler(lambda c: c.data == "skip_requirements", state=AddJurnalStates.waiting_for_requirements)
@dp.message_handler(state=AddJurnalStates.waiting_for_requirements)
async def finish_add_jurnal(message_or_callback, state: FSMContext):
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            requirements = None
            message = message_or_callback.message
        else:
            requirements = message_or_callback.text.strip()
            # URL validatsiyasi
            if requirements and not validate_url(requirements):
                await message_or_callback.answer(
                    "❌ <b>Noto'g'ri URL format!</b>\n\n"
                    "✅ <b>To'g'ri misollar:</b>\n"
                    "• https://journal.uz/requirements\n"
                    "• https://journal.uz/guidelines\n\n"
                    "URL ni https:// yoki http:// bilan boshlang!",
                    parse_mode=ParseMode.HTML
                )
                return  # Bu yerda return bo'lishi kerak
            message = message_or_callback

        await state.update_data(talablar_link=requirements)

        data = await state.get_data()

        jurnal_id = add_jurnal(
            fan_id=data['fan_id'],
            bolim_id=data['bolim_id'],
            nomi=data['nomi'],
            rasmi=data.get('rasmi'),
            nashr_chastotasi=data.get('nashr_chastotasi'),
            jurnal_sayti=data.get('jurnal_sayti'),
            murojaat_link=data.get('murojaat_link'),
            talablar_link=data.get('talablar_link')
        )

        # Ma'lumotlarni chiroyli ko'rsatish
        display_info = "✅ <b>Jurnal muvaffaqiyatli qo'shildi!</b>\n\n"
        display_info += f"📖 <b>Nom:</b> {data['nomi']}\n"
        display_info += f"🆔 <b>ID:</b> {jurnal_id}\n"

        if data.get('nashr_chastotasi'):
            display_info += f"📅 <b>Nashr chastotasi:</b> {data['nashr_chastotasi']}\n"

        if data.get('jurnal_sayti'):
            display_info += f"🌐 <b>Sayt:</b> {data['jurnal_sayti']}\n"

        if data.get('murojaat_link'):
            display_info += f"📧 <b>Murojaat:</b> {data['murojaat_link']}\n"

        if data.get('talablar_link'):
            display_info += f"📋 <b>Talablar:</b> {data['talablar_link']}\n"

        await message.answer(display_info, parse_mode=ParseMode.HTML)

        logging.info(f"Yangi jurnal qo'shildi: {data['nomi']} (ID: {jurnal_id})")

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
        logging.error(f"Jurnal qo'shishda xatolik: {str(e)}")
    finally:
        await state.finish()


# ================ JURNAL TAHRIRLASH ================

@dp.callback_query_handler(lambda c: c.data == "admin_edit_jurnal", state="*")
async def edit_select_fan(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not is_admin(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ Ruxsat yo'q!", show_alert=True)
        return

    try:
        fanlar = get_fanlar()

        keyboard = InlineKeyboardMarkup(row_width=1)
        for fan in fanlar:
            fan_nomi = fan['nomi']
            emoji_map = {
                "Fizika-matematika fanlari": "🔬",
                "Kimyo fanlari": "⚗️",
                "Biologiya fanlari": "🧬",
                "Geologiya-mineralogiya fanlari": "⛰️",
                "Texnika fanlari": "⚙️",
                "Qishloq xo'jaligi fanlari": "🌾",
                "Tarix fanlari": "📜",
                "Iqtisodiyot fanlari": "💰",
                "Falsafa fanlari": "🤔",
                "Filologiya fanlari": "📚",
                "Geografiya fanlari": "🌍",
                "Yuridik fanlar": "⚖️",
                "Pedagogika fanlari": "👨‍🏫",
                "Tibbiyot fanlari": "🏥",
                "Farmatsevtika fanlari": "💊",
                "Veterinariya fanlari": "🐕‍🦺",
                "San'atshunoslik fanlari": "🎨",
                "Arxitektura": "🏗️",
                "Psixologiya fanlari": "🧠",
                "Harbiy fanlar": "🎖️",
                "Sotsiologiya fanlari": "👥",
                "Siyosiy fanlar": "🗳️",
                "Islomshunoslik fanlari": "☪️"
            }
            emoji = emoji_map.get(fan_nomi, "📖")
            if len(fan_nomi) > 25:
                fan_nomi = fan_nomi[:22] + "..."

            keyboard.add(InlineKeyboardButton(f"{emoji} {fan_nomi}", callback_data=f"edit_select_fan_{fan['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_admin"))

        await bot.edit_message_text(
            text="✏️ **JURNAL TAHRIRLASH**\n\nFanni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"Tahrirlash uchun fan tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('edit_select_fan_') and not c.data.startswith('add_select_fan_'), state="*")
async def edit_select_bolim(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        fan_id = int(callback_query.data.split('_')[3])

        bolimlar = get_bolimlar()

        keyboard = InlineKeyboardMarkup(row_width=1)
        for bolim in bolimlar:
            bolim_nomi = bolim['nomi']
            emoji_map = {
                "Milliy nashrlar": "🇺🇿",
                "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari": "🤝",
                "Evropa mamlakatlari nashrlari": "🇪🇺",
                "Amerika mamlakatlari nashrlari": "🌎"
            }
            emoji = emoji_map.get(bolim_nomi, "📄")

            if bolim_nomi == "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari":
                display_name = "🤝 MDH nashrlari"
            elif len(bolim_nomi) > 25:
                display_name = f"{emoji} {bolim_nomi[:22]}..."
            else:
                display_name = f"{emoji} {bolim_nomi}"

            keyboard.add(InlineKeyboardButton(display_name, callback_data=f"edit_select_bolim_{fan_id}_{bolim['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="admin_edit_jurnal"))

        await bot.edit_message_text(
            text="🏛️ Bo'limni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Tahrirlash uchun bo'lim tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('edit_select_bolim_'), state="*")
async def edit_select_jurnal(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = callback_query.data.split('_')
        fan_id = int(data_parts[3])
        bolim_id = int(data_parts[4])

        jurnallar, _ = get_jurnallar(fan_id, bolim_id, 1, 50)

        if not jurnallar:
            await bot.answer_callback_query(callback_query.id, "Bu bo'limda jurnallar mavjud emas!", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(row_width=1)
        for jurnal in jurnallar:
            jurnal_nomi = jurnal['nomi']
            if len(jurnal_nomi) > 40:
                jurnal_nomi = jurnal_nomi[:37] + "..."
            keyboard.add(InlineKeyboardButton(f"📖 {jurnal_nomi}", callback_data=f"edit_jurnal_{jurnal['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=f"edit_select_fan_{fan_id}"))

        await bot.edit_message_text(
            text="📖 Tahrirlash uchun jurnalni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Tahrirlash uchun jurnal tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('edit_jurnal_'), state="*")
async def edit_jurnal_fields(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    try:
        jurnal_id = int(callback_query.data.split('_')[2])
        jurnal = get_jurnal_by_id(jurnal_id)

        if not jurnal:
            await bot.answer_callback_query(callback_query.id, "Jurnal topilmadi!", show_alert=True)
            return

        await state.update_data(jurnal_id=jurnal_id)

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📝 Nom", callback_data="edit_field_nomi"),
            InlineKeyboardButton("🖼️ Rasm", callback_data="edit_field_rasmi"),
            InlineKeyboardButton("📅 Nashr chastotasi", callback_data="edit_field_nashr_chastotasi"),
            InlineKeyboardButton("🌐 Jurnal sayti", callback_data="edit_field_jurnal_sayti"),
            InlineKeyboardButton("📧 Murojaat link", callback_data="edit_field_murojaat_link"),
            InlineKeyboardButton("📋 Talablar link", callback_data="edit_field_talablar_link")
        )
        keyboard.add(
            InlineKeyboardButton("🔙 Orqaga", callback_data=f"edit_select_bolim_{jurnal['fan_id']}_{jurnal['bolim_id']}"))

        text = f"""
✏️ **JURNAL TAHRIRLASH**

📖 **Joriy ma'lumotlar:**
Nom: {jurnal['nomi']}
Fan: {jurnal['fan_nomi']}
Bo'lim: {jurnal['bolim_nomi']}
Nashr chastotasi: {jurnal['nashr_chastotasi'] or 'Kiritilmagan'}
Jurnal sayti: {jurnal['jurnal_sayti'] or 'Kiritilmagan'}

Tahrirlash uchun maydonni tanlang:
"""

        await bot.edit_message_text(
            text=text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        await EditJurnalStates.waiting_for_new_value.set()
    except Exception as e:
        logging.error(f"Tahrirlash maydoni tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.message_handler(content_types=['text', 'photo'], state=EditJurnalStates.waiting_for_new_value)
async def update_jurnal_field(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        jurnal_id = data['jurnal_id']
        field = data['field']

        if field == 'rasmi' and message.content_type == 'photo':
            new_value = message.photo[-1].file_id
        elif field != 'rasmi' and message.content_type == 'text':
            new_value = message.text.strip()
        else:
            await message.answer("❌ Noto'g'ri fayl turi!")
            return

        success = update_jurnal(jurnal_id, **{field: new_value})

        if success:
            await message.answer("✅ Jurnal muvaffaqiyatli yangilandi!")
            logging.info(f"Jurnal yangilandi: ID {jurnal_id}, maydon: {field}")
        else:
            await message.answer("❌ Jurnalni yangilashda xatolik yuz berdi!")

    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
        logging.error(f"Jurnal yangilashda xatolik: {str(e)}")
    finally:
        await state.finish()


# ================ JURNAL O'CHIRISH ================

@dp.callback_query_handler(lambda c: c.data == "admin_delete_jurnal", state="*")
async def delete_select_fan(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not is_admin(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ Ruxsat yo'q!", show_alert=True)
        return

    try:
        fanlar = get_fanlar()

        keyboard = InlineKeyboardMarkup(row_width=1)
        for fan in fanlar:
            fan_nomi = fan['nomi']
            emoji_map = {
                "Fizika-matematika fanlari": "🔬",
                "Kimyo fanlari": "⚗️",
                "Biologiya fanlari": "🧬",
                "Geologiya-mineralogiya fanlari": "⛰️",
                "Texnika fanlari": "⚙️",
                "Qishloq xo'jaligi fanlari": "🌾",
                "Tarix fanlari": "📜",
                "Iqtisodiyot fanlari": "💰",
                "Falsafa fanlari": "🤔",
                "Filologiya fanlari": "📚",
                "Geografiya fanlari": "🌍",
                "Yuridik fanlar": "⚖️",
                "Pedagogika fanlari": "👨‍🏫",
                "Tibbiyot fanlari": "🏥",
                "Farmatsevtika fanlari": "💊",
                "Veterinariya fanlari": "🐕‍🦺",
                "San'atshunoslik fanlari": "🎨",
                "Arxitektura": "🏗️",
                "Psixologiya fanlari": "🧠",
                "Harbiy fanlar": "🎖️",
                "Sotsiologiya fanlari": "👥",
                "Siyosiy fanlar": "🗳️",
                "Islomshunoslik fanlari": "☪️"
            }
            emoji = emoji_map.get(fan_nomi, "📖")
            if len(fan_nomi) > 25:
                fan_nomi = fan_nomi[:22] + "..."

            keyboard.add(InlineKeyboardButton(f"{emoji} {fan_nomi}", callback_data=f"delete_select_fan_{fan['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_admin"))

        await bot.edit_message_text(
            text="🗑️ **JURNAL O'CHIRISH**\n\nFanni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"O'chirish uchun fan tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('delete_select_fan_'), state="*")
async def delete_select_bolim(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        fan_id = int(callback_query.data.split('_')[3])

        bolimlar = get_bolimlar()

        keyboard = InlineKeyboardMarkup(row_width=1)
        for bolim in bolimlar:
            bolim_nomi = bolim['nomi']
            emoji_map = {
                "Milliy nashrlar": "🇺🇿",
                "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari": "🤝",
                "Evropa mamlakatlari nashrlari": "🇪🇺",
                "Amerika mamlakatlari nashrlari": "🌎"
            }
            emoji = emoji_map.get(bolim_nomi, "📄")

            if bolim_nomi == "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari":
                display_name = "🤝 MDH nashrlari"
            elif len(bolim_nomi) > 25:
                display_name = f"{emoji} {bolim_nomi[:22]}..."
            else:
                display_name = f"{emoji} {bolim_nomi}"

            keyboard.add(InlineKeyboardButton(display_name, callback_data=f"delete_select_bolim_{fan_id}_{bolim['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="admin_delete_jurnal"))

        await bot.edit_message_text(
            text="🏛️ Bo'limni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"O'chirish uchun bo'lim tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('delete_select_bolim_'), state="*")
async def delete_select_jurnal(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = callback_query.data.split('_')
        fan_id = int(data_parts[3])
        bolim_id = int(data_parts[4])

        jurnallar, _ = get_jurnallar(fan_id, bolim_id, 1, 50)

        if not jurnallar:
            await bot.answer_callback_query(callback_query.id, "Bu bo'limda jurnallar mavjud emas!", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(row_width=1)
        for jurnal in jurnallar:
            jurnal_nomi = jurnal['nomi']
            if len(jurnal_nomi) > 40:
                jurnal_nomi = jurnal_nomi[:37] + "..."
            keyboard.add(InlineKeyboardButton(f"🗑️ {jurnal_nomi}", callback_data=f"delete_jurnal_{jurnal['id']}"))

        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=f"delete_select_fan_{fan_id}"))

        await bot.edit_message_text(
            text="🗑️ O'chirish uchun jurnalni tanlang:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"O'chirish uchun jurnal tanlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('delete_jurnal_'), state="*")
async def confirm_delete_jurnal(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        jurnal_id = int(callback_query.data.split('_')[2])
        jurnal = get_jurnal_by_id(jurnal_id)

        if not jurnal:
            await bot.answer_callback_query(callback_query.id, "Jurnal topilmadi!", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_delete_{jurnal_id}"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"cancel_delete_{jurnal['fan_id']}_{jurnal['bolim_id']}")
        )

        text = f"""
🗑️ **JURNAL O'CHIRISH**

⚠️ **DIQQAT!** Quyidagi jurnalni o'chirishni tasdiqlaysizmi?

📖 **Nom:** {jurnal['nomi']}
🎓 **Fan:** {jurnal['fan_nomi']}
🏛️ **Bo'lim:** {jurnal['bolim_nomi']}

Bu amalni qaytarib bo'lmaydi!
"""

        await bot.edit_message_text(
            text=text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"O'chirish tasdiqlashda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_delete_'), state="*")
async def execute_delete_jurnal(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        jurnal_id = int(callback_query.data.split('_')[2])
        jurnal = get_jurnal_by_id(jurnal_id)

        if not jurnal:
            await bot.answer_callback_query(callback_query.id, "Jurnal topilmadi!", show_alert=True)
            return

        success = delete_jurnal(jurnal_id)

        if success:
            await bot.edit_message_text(
                text=f"✅ Jurnal muvaffaqiyatli o'chirildi!\n\n📖 {jurnal['nomi']}",
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id
            )
            logging.info(f"Jurnal o'chirildi: {jurnal['nomi']} (ID: {jurnal_id})")
        else:
            await bot.edit_message_text(
                text="❌ Jurnalni o'chirishda xatolik yuz berdi!",
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id
            )

    except Exception as e:
        await bot.edit_message_text(
            text=f"❌ Xatolik: {str(e)}",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )
        logging.error(f"Jurnal o'chirishda xatolik: {str(e)}")


@dp.callback_query_handler(lambda c: c.data.startswith('cancel_delete_'), state="*")
async def cancel_delete_jurnal(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data_parts = callback_query.data.split('_')
        fan_id = int(data_parts[2])
        bolim_id = int(data_parts[3])

        await bot.edit_message_text(
            text="❌ O'chirish bekor qilindi.",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )

        # 2 soniya kutib, bo'limlar ro'yxatiga qaytarish
        await asyncio.sleep(2)

        # Bo'limlar ro'yxatiga qaytarish
        fake_callback = types.CallbackQuery(
            id=callback_query.id,
            from_user=callback_query.from_user,
            chat_instance=callback_query.chat_instance,
            data=f"delete_select_fan_{fan_id}",
            message=callback_query.message
        )
        await delete_select_bolim(fake_callback, state)
    except Exception as e:
        logging.error(f"O'chirishni bekor qilishda xatolik: {e}")


# ================ YORDAMCHI FUNKSIYALAR ================

# Admin paneliga qaytish
@dp.callback_query_handler(lambda c: c.data == "back_to_admin", state="*")
async def back_to_admin_panel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    try:
        stats = get_statistics()

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
        )
        keyboard.add(
            InlineKeyboardButton("➕ Jurnal qo'shish", callback_data="admin_add_jurnal"),
            InlineKeyboardButton("✏️ Jurnal tahrirlash", callback_data="admin_edit_jurnal")
        )
        keyboard.add(
            InlineKeyboardButton("🗑️ Jurnal o'chirish", callback_data="admin_delete_jurnal")
        )

        text = f"""
🔧 **ADMIN PANEL**

📊 **Tezkor statistika:**
👥 Foydalanuvchilar: {stats['users_count']}
📚 Jurnallar: {stats['jurnallar_count']}
🎓 Fanlar: {stats['fanlar_count']}
🏛️ Bo'limlar: {stats['bolimlar_count']}

Kerakli amalni tanlang:
"""

        await bot.edit_message_text(
            text=text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"Admin paneliga qaytishda xatolik: {e}")
        await bot.answer_callback_query(callback_query.id, "❌ Xatolik yuz berdi!", show_alert=True)


# Xatolik yuz berganda state ni tozalash
@dp.errors_handler()
async def error_handler(update, exception):
    logging.error(f"Xatolik yuz berdi: {exception}")
    return True
