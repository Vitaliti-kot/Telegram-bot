from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Таблица допусков
TOLERANCES = {
    (1, 3): {
        "h6": (-6, 0),
        "g6": (-8, -2),
        "H7": (0, 10),
        "js6": (-3, 3),
    },

    (3, 6): {
        "h6": (-8, 0),
        "g6": (-12, -4),
        "H7": (0, 12),
        "js6": (-4, 4),
    },

    (6, 10): {
        "h6": (-9, 0),
        "g6": (-14, -5),
        "H7": (0, 15),
        "js6": (-4.5, 4.5),
    },
}

user_data = {}


def find_tolerance(diameter, field):
    for (d_min, d_max), values in TOLERANCES.items():
        if d_min <= diameter <= d_max:
            if field in values:
                return values[field]
    return None


def main_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(text="Ввести диаметр", callback_data="diameter")
    builder.button(text="Выбрать допуск", callback_data="field")
    builder.button(text="Рассчитать", callback_data="calc")

    builder.adjust(1)

    return builder.as_markup()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Бот допусков и посадок

"
        "1. Введите диаметр
"
        "2. Выберите поле допуска
"
        "3. Нажмите 'Рассчитать'",
        reply_markup=main_keyboard()
    )


@dp.callback_query(F.data == "diameter")
async def diameter_button(callback: CallbackQuery):
    user_data[callback.from_user.id] = {
        "mode": "wait_diameter"
    }

    await callback.message.answer("Введите диаметр в мм")
    await callback.answer()


@dp.callback_query(F.data == "field")
async def field_button(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    fields = ["h6", "g6", "H7", "js6"]

    for field in fields:
        builder.button(text=field, callback_data=f"field_{field}")

    builder.adjust(2)

    await callback.message.answer(
        "Выберите поле допуска",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("field_"))
async def field_selected(callback: CallbackQuery):
    field = callback.data.replace("field_", "")

    if callback.from_user.id not in user_data:
        user_data[callback.from_user.id] = {}

    user_data[callback.from_user.id]["field"] = field

    await callback.message.answer(f"Выбран допуск: {field}")
    await callback.answer()


@dp.callback_query(F.data == "calc")
async def calculate(callback: CallbackQuery):
    data = user_data.get(callback.from_user.id)

    if not data:
        await callback.message.answer("Сначала введите данные")
        return

    if "diameter" not in data or "field" not in data:
        await callback.message.answer("Не хватает данных")
        return

    diameter = data["diameter"]
    field = data["field"]

    result = find_tolerance(diameter, field)

    if not result:
        await callback.message.answer("Нет данных в таблице")
        return

    low, high = result

    min_size = diameter + low / 1000
    max_size = diameter + high / 1000

    answer = (
        f"Диаметр: {diameter} мм
"
        f"Допуск: {field}

"
        f"Нижнее отклонение: {low} мкм
"
        f"Верхнее отклонение: {high} мкм

"
        f"Минимальный размер: {min_size:.3f} мм
"
        f"Максимальный размер: {max_size:.3f} мм"
    )

    await callback.message.answer(answer)
    await callback.answer()


@dp.message()
async def messages(message: Message):
    data = user_data.get(message.from_user.id)

    if not data:
        return

    if data.get("mode") == "wait_diameter":
        try:
            diameter = float(message.text.replace(',', '.'))

            user_data[message.from_user.id]["diameter"] = diameter
            user_data[message.from_user.id]["mode"] = "done"

            await message.answer(
                f"Диаметр сохранён: {diameter} мм",
                reply_markup=main_keyboard()
            )

        except:
            await message.answer("Ошибка ввода")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())