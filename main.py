import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (замените на свой)
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Инициализация бота с правильными параметрами
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# База данных для хранения social credit
social_credit_db = {}

# Разрешенный пользователь
ALLOWED_USER = "@Zhdanov_Albert"

def is_user_allowed(user: types.User):
    """Проверяет, имеет ли пользователь права доступа"""
    return user.username == ALLOWED_USER.lstrip('@') or f"@{user.username}" == ALLOWED_USER

async def get_target_user(message: Message, args: str) -> types.User | None:
    """Определяет целевого пользователя по reply или аргументам"""
    # Если есть reply - берем этого пользователя
    if message.reply_to_message:
        return message.reply_to_message.from_user
    
    # Если указан username в аргументах
    if args and args.startswith('@'):
        username = args.lstrip('@').split()[0]  # Берем только первое слово после @
        # В реальном боте здесь нужно использовать API Telegram
        return types.User(
            id=hash(username),
            first_name=username,
            username=username,
            is_bot=False,
            language_code='ru'
        )
    
    # Если нет аргументов - возвращаем отправителя
    return message.from_user

async def parse_command_args(message: Message) -> tuple[types.User | None, int]:
    """Парсит аргументы команд изменения кредита"""
    command_text = message.text.split(maxsplit=1)
    args = command_text[1] if len(command_text) > 1 else ""
    
    # Парсим количество (по умолчанию 1)
    amount = 1
    if args and args.split()[0].isdigit():
        amount = int(args.split()[0])
        args = " ".join(args.split()[1:])
    
    # Получаем целевого пользователя
    target_user = await get_target_user(message, args)
    
    return target_user, amount

# ========== КОМАНДЫ ========== #

@dp.message(Command("прибавить_social_credit"))
async def add_social_credit(message: Message):
    if not is_user_allowed(message.from_user):
        await message.answer("⛔ У вас нет доступа к этой команде!")
        return

    target_user, amount = await parse_command_args(message)
    
    if target_user is None:
        await message.answer(
            "ℹ Укажите пользователя:\n"
            "1. Ответьте на его сообщение\n"
            "2. Укажите @username после суммы\n\n"
            "Пример: <code>/прибавить_social_credit 5 @username</code>"
        )
        return

    user_id = target_user.id
    social_credit_db[user_id] = social_credit_db.get(user_id, 0) + amount
    
    await message.answer(
        f"✅ Пользователю {hbold(target_user.full_name)} добавлено {amount} социальных кредитов!\n"
        f"📊 Текущий баланс: {social_credit_db[user_id]}"
    )

@dp.message(Command("убавить_social_credit"))
async def remove_social_credit(message: Message):
    if not is_user_allowed(message.from_user):
        await message.answer("⛔ У вас нет доступа к этой команде!")
        return

    target_user, amount = await parse_command_args(message)
    
    if target_user is None:
        await message.answer(
            "ℹ Укажите пользователя:\n"
            "1. Ответьте на его сообщение\n"
            "2. Укажите @username после суммы\n\n"
            "Пример: <code>/убавить_social_credit 3 @username</code>"
        )
        return

    user_id = target_user.id
    social_credit_db[user_id] = social_credit_db.get(user_id, 0) - amount
    
    await message.answer(
        f"⚠ Пользователю {hbold(target_user.full_name)} убавлено {amount} социальных кредитов!\n"
        f"📊 Текущий баланс: {social_credit_db[user_id]}"
    )

@dp.message(Command("getsocialcredit"))
async def check_social_credit(message: Message):
    command_text = message.text.split(maxsplit=1)
    args = command_text[1] if len(command_text) > 1 else ""
    
    target_user = await get_target_user(message, args)
    
    if target_user is None:
        target_user = message.from_user
    
    credit = social_credit_db.get(target_user.id, 0)
    await message.answer(
        f"📊 Социальный кредит пользователя {hbold(target_user.full_name)}:\n"
        f"⭐ {credit} очков"
    )

@dp.message(Command("изгнать"))
async def ban_user(message: Message):
    if not is_user_allowed(message.from_user):
        await message.answer("⛔ У вас нет доступа к этой команде!")
        return

    command_text = message.text.split(maxsplit=1)
    args = command_text[1] if len(command_text) > 1 else ""
    
    target_user = await get_target_user(message, args)
    
    if target_user is None:
        await message.answer(
            "ℹ Укажите пользователя:\n"
            "1. Ответьте на его сообщение\n"
            "2. Укажите @username\n\n"
            "Пример: <code>/изгнать @username</code>"
        )
        return

    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id
        )
        await message.answer(f"☠ Пользователь {hbold(target_user.full_name)} был изгнан!")
    except Exception as e:
        logger.error(f"Ошибка при изгнании: {e}")
        await message.answer("❌ Не удалось изгнать пользователя. Проверьте права бота.")

# ========== ЗАПУСК ========== #

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
