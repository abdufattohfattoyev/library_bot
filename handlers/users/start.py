from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from loader import dp, bot
from utils.db_api.users import get_user, add_user, update_user_activity
from utils.db_api.jurnallar import (
    get_fanlar, get_bolimlar, get_fan_by_id, get_bolim_by_id,
    get_jurnallar_count_by_fan_bolim, get_jurnallar, get_jurnal_by_id
)
import logging

# Majburiy obuna sozlamalari
REQUIRED_CHANNELS = [
    {"name": "Jurnal Universal", "username": "@jurnal_universal", "url": "https://t.me/jurnal_universal"},
    {"name": "Guruh", "username": "+gLy1cprxw1gwNDVi", "url": "https://t.me/+gLy1cprxw1gwNDVi", "chat_id": None}
    # Guruh ID sini keyinroq o'rnatish kerak
]

# Emoji xaritalari
FAN_EMOJI_MAP = {
    "Fizika-matematika fanlari": ("🔬", "Fizika-matem..."),
    "Kimyo fanlari": ("⚗️", "Kimyo fanlari"),
    "Biologiya fanlari": ("🧬", "Biologiya fanlari"),
    "Geologiya-mineralogiya fanlari": ("⛰️", "Geologiya-min..."),
    "Texnika fanlari": ("⚙️", "Texnika fanlari"),
    "Qishloq xo'jaligi fanlari": ("🌾", "Qishloq x..."),
    "Tarix fanlari": ("📜", "Tarix fanlari"),
    "Iqtisodiyot fanlari": ("💰", "Iqtisodiyot"),
    "Falsafa fanlari": ("🤔", "Falsafa fanlari"),
    "Filologiya fanlari": ("📚", "Filologiya"),
    "Geografiya fanlari": ("🌍", "Geografiya"),
    "Yuridik fanlar": ("⚖️", "Yuridik fanlar"),
    "Pedagogika fanlari": ("👨‍🏫", "Pedagogika"),
    "Tibbiyot fanlari": ("🏥", "Tibbiyot fanlari"),
    "Farmatsevtika fanlari": ("💊", "Farmatsevtika"),
    "Veterinariya fanlari": ("🐕‍🦺", "Veterinariya"),
    "San'atshunoslik fanlari": ("🎨", "San'atshunoslik"),
    "Arxitektura": ("🏗️", "Arxitektura"),
    "Psixologiya fanlari": ("🧠", "Psixologiya"),
    "Harbiy fanlar": ("🎖️", "Harbiy fanlar"),
    "Sotsiologiya fanlari": ("👥", "Sotsiologiya"),
    "Siyosiy fanlar": ("🗳️", "Siyosiy fanlar"),
    "Islomshunoslik fanlari": ("☪️", "Islomshunoslik")
}

BOLIM_EMOJI_MAP = {
    "Milliy nashrlar": ("🇺🇿", "Milliy nashrlar"),
    "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari": ("🤝", "MDH nashrlari"),
    "Evropa mamlakatlari nashrlari": ("🇪🇺", "Evropa nashrlari"),
    "Amerika mamlakatlari nashrlari": ("🌎", "Amerika nashrlari")
}


async def check_subscription(user_id):
    """Foydalanuvchining obuna holatini tekshirish va obuna bo'lmagan kanallarni qaytarish"""
    unsubscribed_channels = []

    for channel in REQUIRED_CHANNELS:
        try:
            if channel.get('chat_id'):
                # Guruh uchun
                member = await bot.get_chat_member(chat_id=channel['chat_id'], user_id=user_id)
            else:
                # Kanal uchun
                member = await bot.get_chat_member(chat_id=channel['username'], user_id=user_id)

            if member.status in ['left', 'kicked']:
                unsubscribed_channels.append(channel)

        except Exception as e:
            logging.error(f"Obuna holatini tekshirishda xatolik: {e}")
            unsubscribed_channels.append(channel)

    # Agar birorta ham obuna bo'lmagan kanal yo'q bo'lsa - True qaytaramiz
    # Aks holda False va obuna bo'lmagan kanallar ro'yxatini qaytaramiz
    if len(unsubscribed_channels) == 0:
        return True, []
    else:
        return False, unsubscribed_channels


def create_subscription_keyboard(unsubscribed_channels):
    """Faqat obuna bo'lmagan kanallar uchun tugmalarni yaratish"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel in unsubscribed_channels:
        keyboard.add(InlineKeyboardButton(
            text=f"🔗 {channel['name']}",
            url=channel['url']
        ))

    keyboard.add(InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription"))
    return keyboard


async def send_subscription_message(message_or_query, unsubscribed_channels, is_callback=False):
    """Obuna xabarini yuborish - faqat obuna bo'lmagan kanallarni ko'rsatish"""
    if len(unsubscribed_channels) == 1:
        text = f"Botdan foydalanish uchun pasdagi {unsubscribed_channels[0]['name']} ga a'zo bo'ling"
    else:
        text = "Botdan foydalanish uchun pasdagi kanal va gruppaga a'zo bo'ling"

    keyboard = create_subscription_keyboard(unsubscribed_channels)

    if is_callback:
        await safe_edit_message(message_or_query.message, text, keyboard, ParseMode.HTML)
    else:
        await message_or_query.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


def get_fan_display(fan_nomi, max_length=18):
    """Fan nomini emoji bilan formatlash"""
    if fan_nomi in FAN_EMOJI_MAP:
        emoji, qisqa_nom = FAN_EMOJI_MAP[fan_nomi]
        return f"{emoji} {qisqa_nom}"
    else:
        if len(fan_nomi) > max_length:
            fan_nomi = fan_nomi[:max_length - 3] + "..."
        return f"📖 {fan_nomi}"


def get_bolim_display(bolim_nomi, max_length=20):
    """Bo'lim nomini emoji bilan formatlash"""
    if bolim_nomi in BOLIM_EMOJI_MAP:
        emoji, qisqa_nom = BOLIM_EMOJI_MAP[bolim_nomi]
        return f"{emoji} {qisqa_nom}"
    else:
        if len(bolim_nomi) > max_length:
            bolim_nomi = bolim_nomi[:max_length - 3] + "..."
        return f"📄 {bolim_nomi}"


async def safe_delete_message(chat_id, message_id):
    """Xabarni xavfsiz o'chirish"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.error(f"Xabarni o'chirishda xatolik: {e}")


async def safe_edit_message(message, text, keyboard=None, parse_mode=None):
    """Xabarni xavfsiz tahrirlash"""
    try:
        if message.photo:
            # Agar rasm bo'lsa, caption tahrirlash
            await bot.edit_message_caption(
                caption=text,
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
        else:
            # Oddiy matn bo'lsa
            await bot.edit_message_text(
                text=text,
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
    except Exception as e:
        logging.error(f"Xabarni tahrirlashda xatolik: {e}")
        # Xatolik bo'lsa, yangi xabar yuborish
        await message.answer(text=text, reply_markup=keyboard, parse_mode=parse_mode)


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    # Obuna holatini tekshirish
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(message, unsubscribed_channels)
        return

    # Foydalanuvchini bazaga qo'shish yoki yangilash
    user = get_user(user_id)
    if not user:
        add_user(user_id, full_name, username)
        logging.info(f"Yangi foydalanuvchi qo'shildi: {full_name} (@{username})")
    else:
        update_user_activity(user_id)

    # Fanlar ro'yxatini olish
    fanlar = get_fanlar()

    # Inline keyboard yaratish
    keyboard = InlineKeyboardMarkup(row_width=2)

    for fan in fanlar:
        btn_text = get_fan_display(fan['nomi'])
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=f"fan_{fan['id']}"
        )
        keyboard.insert(btn)

    welcome_text = f"""🎓 <b>Assalomu alaykum, {full_name}!</b>

Ilmiy jurnallar botiga xush kelibsiz!

Bu bot orqali turli fanlar bo'yicha ilmiy jurnallar haqida ma'lumot olishingiz mumkin.

📚 <b>Fanni tanlang:</b>"""

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data == 'check_subscription')
async def check_subscription_callback(callback_query: types.CallbackQuery):
    """Obunani tekshirish callback"""
    await bot.answer_callback_query(callback_query.id)

    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)

    if not is_subscribed:
        # Hali ham obuna bo'lmagan kanallar bor
        if len(unsubscribed_channels) == 1:
            error_text = f"❌ Siz hali {unsubscribed_channels[0]['name']} ga obuna bo'lmagansiz!"
        else:
            channel_names = ", ".join([ch['name'] for ch in unsubscribed_channels])
            error_text = f"❌ Siz hali quyidagi kanallarga obuna bo'lmagansiz: {channel_names}"

        await bot.answer_callback_query(
            callback_query.id,
            error_text,
            show_alert=True
        )
        # Obuna bo'lmagan kanallarni yangilab ko'rsatish
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    # Agar hamma kanallarga obuna bo'lgan bo'lsa, asosiy menyuga o'tkazish
    await bot.answer_callback_query(callback_query.id, "✅ Obuna tasdiqlandi!")

    # Foydalanuvchini bazaga qo'shish yoki yangilash
    full_name = callback_query.from_user.full_name
    username = callback_query.from_user.username

    user = get_user(user_id)
    if not user:
        add_user(user_id, full_name, username)
        logging.info(f"Yangi foydalanuvchi qo'shildi: {full_name} (@{username})")
    else:
        update_user_activity(user_id)

    # Fanlar ro'yxatini olish
    fanlar = get_fanlar()

    # Inline keyboard yaratish
    keyboard = InlineKeyboardMarkup(row_width=2)

    for fan in fanlar:
        btn_text = get_fan_display(fan['nomi'])
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=f"fan_{fan['id']}"
        )
        keyboard.insert(btn)

    welcome_text = f"""🎓 <b>Assalomu alaykum, {full_name}!</b>

Ilmiy jurnallar botiga xush kelibsiz!

Bu bot orqali turli fanlar bo'yicha ilmiy jurnallar haqida ma'lumot olishingiz mumkin.

📚 <b>Fanni tanlang:</b>"""

    await safe_edit_message(callback_query.message, welcome_text, keyboard, ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data.startswith('fan_'))
async def show_bolimlar(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Obuna holatini tekshirish
    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    update_user_activity(callback_query.from_user.id)

    fan_id = int(callback_query.data.split('_')[1])
    fan = get_fan_by_id(fan_id)
    bolimlar = get_bolimlar()

    if not fan:
        await bot.answer_callback_query(callback_query.id, "Fan topilmadi!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(row_width=1)

    for bolim in bolimlar:
        count = get_jurnallar_count_by_fan_bolim(fan_id, bolim['id'])
        btn_text = f"{get_bolim_display(bolim['nomi'])} ({count})"

        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=f"bolim_{fan_id}_{bolim['id']}_1"
        )
        keyboard.add(btn)

    # Orqaga qaytish tugmasi
    keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_fanlar"))

    # Fan nomini qisqartirish
    fan_nomi = fan['nomi']
    if len(fan_nomi) > 30:
        fan_nomi = fan_nomi[:27] + "..."

    text = f"📖 <b>{fan_nomi}</b>\n\nBo'limni tanlang:"

    await safe_edit_message(callback_query.message, text, keyboard, ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data.startswith('bolim_'))
async def show_jurnallar(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Obuna holatini tekshirish
    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    update_user_activity(callback_query.from_user.id)

    data_parts = callback_query.data.split('_')
    fan_id = int(data_parts[1])
    bolim_id = int(data_parts[2])
    page = int(data_parts[3])

    fan = get_fan_by_id(fan_id)
    bolim = get_bolim_by_id(bolim_id)

    if not fan or not bolim:
        await bot.answer_callback_query(callback_query.id, "Ma'lumot topilmadi!", show_alert=True)
        return

    # Jurnallar ro'yxatini olish
    jurnallar, total_count = get_jurnallar(fan_id, bolim_id, page, 8)
    total_pages = (total_count + 7) // 8

    # Fan va bo'lim nomlarini formatlash
    fan_display = fan['nomi'][:20] + "..." if len(fan['nomi']) > 20 else fan['nomi']
    bolim_display = get_bolim_display(bolim['nomi'], 15)

    if not jurnallar:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=f"fan_{fan_id}"))

        text = f"📚 <b>{fan_display}</b>\n{bolim_display}\n\n❌ Jurnallar mavjud emas."
        await safe_edit_message(callback_query.message, text, keyboard, ParseMode.HTML)
        return

    # Jurnallar ro'yxati uchun keyboard
    keyboard = InlineKeyboardMarkup(row_width=1)

    for i, jurnal in enumerate(jurnallar, 1):
        jurnal_nomi = jurnal['nomi']
        if len(jurnal_nomi) > 35:
            jurnal_nomi = jurnal_nomi[:32] + "..."

        btn_text = f"{(page - 1) * 8 + i}. {jurnal_nomi}"
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=f"jurnal_{jurnal['id']}"
        )
        keyboard.add(btn)

    # Pagination tugmalari
    if total_pages > 1:
        nav_buttons = []

        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"bolim_{fan_id}_{bolim_id}_{page - 1}"))

        nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))

        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"bolim_{fan_id}_{bolim_id}_{page + 1}"))

        keyboard.row(*nav_buttons)

    # Orqaga qaytish tugmasi
    keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=f"fan_{fan_id}"))

    # Bo'lim nomini qisqartirish
    bolim_short = get_bolim_display(bolim['nomi'], 10)
    text = f"📚 <b>{fan_display}</b>\n{bolim_short}\n\n📖 Jurnallar ({total_count})\n📄 {page}/{total_pages}:"

    await safe_edit_message(callback_query.message, text, keyboard, ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data.startswith('jurnal_'))
async def show_jurnal_detail(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Obuna holatini tekshirish
    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    update_user_activity(callback_query.from_user.id)

    jurnal_id = int(callback_query.data.split('_')[1])
    jurnal = get_jurnal_by_id(jurnal_id)

    if not jurnal:
        await bot.answer_callback_query(callback_query.id, "Jurnal topilmadi!", show_alert=True)
        return

    # Jurnal ma'lumotlarini formatlash
    text = f"📖 <b>{jurnal['nomi']}</b>\n\n"
    text += f"🎓 <b>Fan:</b> {jurnal['fan_nomi']}\n"
    text += f"🏛️ <b>Bo'lim:</b> {jurnal['bolim_nomi']}\n"

    if jurnal['nashr_chastotasi']:
        text += f"📅 <b>Nashr chastotasi:</b> {jurnal['nashr_chastotasi']}\n"

    # Havolalar tugmalari
    keyboard = InlineKeyboardMarkup()

    # Jurnal saytiga o'tish
    if jurnal['jurnal_sayti']:
        keyboard.add(InlineKeyboardButton("🌐 Saytga o'tish", url=jurnal['jurnal_sayti']))

    # Murojaat va Talablar tugmalari
    row_buttons = []
    if jurnal['murojaat_link']:
        row_buttons.append(InlineKeyboardButton("📧 Murojaat", url=jurnal['murojaat_link']))

    if jurnal['talablar_link']:
        row_buttons.append(InlineKeyboardButton("📋 Talablar", url=jurnal['talablar_link']))

    if len(row_buttons) == 2:
        keyboard.row(row_buttons[0], row_buttons[1])
    elif len(row_buttons) == 1:
        keyboard.add(row_buttons[0])

    # Orqaga qaytish tugmasi
    keyboard.add(InlineKeyboardButton(
        "🔙 Orqaga",
        callback_data=f"back_to_jurnallar_{jurnal['fan_id']}_{jurnal['bolim_id']}_1"
    ))

    # Eski xabarni o'chirish
    await safe_delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    # Jurnal ma'lumotlarini yuborish
    if jurnal['rasmi']:
        try:
            await bot.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=jurnal['rasmi'],
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.error(f"Rasm yuklashda xatolik: {e}")
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=text + "\n\n❗️ <i>Rasm yuklanmadi</i>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    else:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )


@dp.callback_query_handler(lambda c: c.data.startswith('back_to_jurnallar_'))
async def back_to_jurnallar(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Obuna holatini tekshirish
    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    update_user_activity(callback_query.from_user.id)

    data_parts = callback_query.data.split('_')
    fan_id = int(data_parts[3])
    bolim_id = int(data_parts[4])
    page = int(data_parts[5])

    # Eski xabarni o'chirish
    await safe_delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    # To'g'ridan-to'g'ri jurnallar ro'yxatini ko'rsatish
    fan = get_fan_by_id(fan_id)
    bolim = get_bolim_by_id(bolim_id)

    if not fan or not bolim:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="❌ Ma'lumot topilmadi!",
            parse_mode=ParseMode.HTML
        )
        return

    # Jurnallar ro'yxatini olish
    jurnallar, total_count = get_jurnallar(fan_id, bolim_id, page, 8)
    total_pages = (total_count + 7) // 8

    # Fan va bo'lim nomlarini formatlash
    fan_display = fan['nomi'][:20] + "..." if len(fan['nomi']) > 20 else fan['nomi']
    bolim_display = get_bolim_display(bolim['nomi'], 15)

    if not jurnallar:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=f"fan_{fan_id}"))

        text = f"📚 <b>{fan_display}</b>\n{bolim_display}\n\n❌ Jurnallar mavjud emas."

        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        return

    # Jurnallar ro'yxati uchun keyboard
    keyboard = InlineKeyboardMarkup(row_width=1)

    for i, jurnal in enumerate(jurnallar, 1):
        jurnal_nomi = jurnal['nomi']
        if len(jurnal_nomi) > 35:
            jurnal_nomi = jurnal_nomi[:32] + "..."

        btn_text = f"{(page - 1) * 8 + i}. {jurnal_nomi}"
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=f"jurnal_{jurnal['id']}"
        )
        keyboard.add(btn)

    # Pagination tugmalari
    if total_pages > 1:
        nav_buttons = []

        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️", callback_data=f"back_to_jurnallar_{fan_id}_{bolim_id}_{page - 1}"))

        nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current_page"))

        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton("➡️", callback_data=f"back_to_jurnallar_{fan_id}_{bolim_id}_{page + 1}"))

        keyboard.row(*nav_buttons)

    # Orqaga qaytish tugmasi
    keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=f"fan_{fan_id}"))

    # Bo'lim nomini qisqartirish
    bolim_short = get_bolim_display(bolim['nomi'], 10)
    text = f"📚 <b>{fan_display}</b>\n{bolim_short}\n\n📖 Jurnallar ({total_count})\n📄 {page}/{total_pages}:"

    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@dp.callback_query_handler(lambda c: c.data == 'back_to_fanlar')
async def back_to_fanlar(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Obuna holatini tekshirish
    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    update_user_activity(callback_query.from_user.id)

    fanlar = get_fanlar()
    keyboard = InlineKeyboardMarkup(row_width=2)

    for fan in fanlar:
        btn_text = get_fan_display(fan['nomi'])
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=f"fan_{fan['id']}"
        )
        keyboard.insert(btn)

    welcome_text = """🎓 <b>Ilmiy jurnallar</b>

📚 <b>Fanni tanlang:</b>"""

    await safe_edit_message(callback_query.message, welcome_text, keyboard, ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data == 'current_page')
async def current_page(callback_query: types.CallbackQuery):
    # Obuna holatini tekshirish
    user_id = callback_query.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        if len(unsubscribed_channels) == 1:
            error_text = f"❌ Avval {unsubscribed_channels[0]['name']} ga obuna bo'ling!"
        else:
            channel_names = ", ".join([ch['name'] for ch in unsubscribed_channels])
            error_text = f"❌ Avval quyidagi kanallarga obuna bo'ling: {channel_names}"

        await bot.answer_callback_query(
            callback_query.id,
            error_text,
            show_alert=True
        )
        await send_subscription_message(callback_query, unsubscribed_channels, is_callback=True)
        return

    await bot.answer_callback_query(callback_query.id, "Joriy sahifa")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    user_id = message.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(message, unsubscribed_channels)
        return

    update_user_activity(message.from_user.id)

    help_text = """🤖 <b>Bot haqida ma'lumot:</b>

Bu bot O'zbekiston Respublikasi Vazirlar Mahkamasining ilmiy jurnallar ro'yxatini ko'rish uchun yaratilgan.

📋 <b>Buyruqlar:</b>
/start - Botni ishga tushirish
/help - Yordam

🎯 <b>Imkoniyatlar:</b>
• 23 ta fan bo'yicha jurnallar
• 4 ta bo'lim 
• Har jurnal haqida to'liq ma'lumot
• Jurnal sayti va talablariga o'tish

📞 <b>Qo'llab-quvvatlash:</b>
Muammo bo'lsa, admin bilan bog'laning."""

    await message.answer(help_text, parse_mode=ParseMode.HTML)


@dp.message_handler()
async def unknown_message(message: types.Message):
    user_id = message.from_user.id
    is_subscribed, unsubscribed_channels = await check_subscription(user_id)
    if not is_subscribed:
        await send_subscription_message(message, unsubscribed_channels)
        return

    update_user_activity(message.from_user.id)

    response_text = """❓ Kechirasiz, bu buyruqni tushunmadim.

Botdan foydalanish uchun /start buyrug'ini yuboring.

Yordam uchun: /help"""

    await message.answer(response_text)