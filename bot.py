import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()
}

if not BOT_TOKEN:
    raise SystemExit("Не задана переменная окружения BOT_TOKEN")

REF_MESSAGE = (
    "🎉 Ваш друг присоединился по ссылке. Вам начислен 1 спин! "
    "Ещё 1 спин получите после 100 сом подтверждённых пополнений друга."
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Реферал")]],
    resize_keyboard=True,
)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Нажмите «Реферал», чтобы получить свою ссылку для друзей.",
        reply_markup=main_kb,
    )


@dp.message(F.text == "Реферал")
async def referral(message: Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(
        f"Ваша реферальная ссылка:\n{link}\n\n"
        "Отправьте её другу — когда он присоединится, вы получите спин."
    )


@dp.message(Command("ref"))
async def cmd_ref(message: Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        return  # не админ — молча игнорируем

    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Использование: /ref <telegram_id>")
        return

    try:
        await bot.send_message(int(arg), REF_MESSAGE)
        await message.answer(f"✅ Сообщение отправлено пользователю {arg}")
    except TelegramForbiddenError:
        await message.answer("❌ Пользователь не запускал бота или заблокировал его.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ Не удалось отправить: {e.message}")


async def setup_menu():
    # Кнопка «Меню»: для всех — /start, для админов ещё и /ref
    await bot.set_my_commands(
        [BotCommand(command="start", description="Запустить бота")],
        scope=BotCommandScopeDefault(),
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(
                [
                    BotCommand(command="start", description="Запустить бота"),
                    BotCommand(command="ref", description="Отправить реф-уведомление"),
                ],
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception as e:
            logging.warning("Не удалось задать меню для %s: %s", admin_id, e)


async def main():
    await setup_menu()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
