import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from models.states import Profile
from models.models import users
from models.config import Settings
from utils.food import calculate_calorie_goal, calculate_water_goal
from utils.api import get_weather, get_food_info

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Используйте команду /set_profile для начала. Введите /help для просмотра доступных команд.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/set_profile - Настройка профиля\n"
        "/log_water <количество> - Записать воду\n"
        "/log_food <продукт> - Записать еду\n"
        "/log_workout <тип> <время> - Записать тренировку\n"
        "/check_progress - Показать прогресс\n"
        "/help - Помощь"
    )

@router.message(Command("set_profile"))
async def start_profile(message: Message, state: FSMContext):
    users[message.chat.id] = {
        'logged_water': 0,
        'logged_calories': 0,
        'burned_calories': 0,
    }
    await message.answer("Введите ваш вес (в кг):")
    await state.set_state(Profile.weight)

@router.message(Profile.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        await state.update_data(weight=float(message.text))
        await message.answer("Введите ваш рост (в см):")
        await state.set_state(Profile.height)
    except:
        await message.answer("Ошибка ввода.")

@router.message(Profile.height)
async def process_height(message: Message, state: FSMContext):
    try:
        await state.update_data(height=float(message.text))
        await message.answer("Введите ваш возраст:")
        await state.set_state(Profile.age)
    except:
        await message.answer("Ошибка ввода.")

@router.message(Profile.age)
async def process_age(message: Message, state: FSMContext):
    try:
        await state.update_data(age=int(message.text))
        await message.answer("Сколько минут активности у вас в день?")
        await state.set_state(Profile.activity)
    except:
        await message.answer("Ошибка ввода.")

@router.message(Profile.activity)
async def process_activity(message: Message, state: FSMContext):
    try:
        await state.update_data(activity=int(message.text))
        await message.answer("В каком городе вы находитесь?")
        await state.set_state(Profile.city)
    except:
        await message.answer("Ошибка ввода.")

@router.message(Profile.city)
async def process_city(message: Message, state: FSMContext):
    user_data = await state.get_data()
    users[message.chat.id].update(user_data)
    
    temperature = await get_weather(message.text)
    
    calorie_goal = calculate_calorie_goal(user_data)
    water_goal = calculate_water_goal(user_data, temperature)
    
    users[message.chat.id]['water_goal'] = water_goal
    users[message.chat.id]['calorie_goal'] = calorie_goal
    
    response = "Профиль сохранён.\n"
    if temperature != 0:
        response += f"Температура в городе {message.text}: {temperature} °C\n"
    response += f"Норма воды: {water_goal} мл\nНорма калорий: {calorie_goal} ккал"
    
    await message.answer(response)
    await state.clear()

@router.message(Command("log_water"))
async def cmd_log_water(message: Message):
    user = users.get(message.chat.id)
    if not user:
        await message.answer("Сначала необходимо настроить профиль.")
        return
    
    try:
        amount = int(message.text.split()[1])
        user['logged_water'] += amount
        remaining = user['water_goal'] - user['logged_water']
        await message.answer(f"Записано {amount} мл воды. Осталось: {max(remaining, 0)} мл.")
    except:
        await message.answer("Использование: /log_water 250")

@router.message(Command("log_food"))
async def cmd_log_food(message: Message):
    user = users.get(message.chat.id)
    if not user:
        await message.answer("Сначала необходимо настроить профиль.")
        return
    
    try:
        product_name = message.text.split(maxsplit=1)[1]
    except:
        await message.answer("Использование: /log_food продукт")
        return
    
    info = await get_food_info(product_name)
    if not info:
        await message.answer("Продукт не найден.")
        return
    
    await message.answer(f"{info['name']}: {info['calories']} ккал на 100 г. Сколько грамм вы съели?")
    
    user['food_calories'] = info['calories']

@router.message(F.text.regexp(r'^\d+$'))
async def process_food_amount(message: Message):
    user = users.get(message.chat.id)
    if not user or 'food_calories' not in user:
        return
    
    try:
        grams = float(message.text)
        calories = grams / 100 * user['food_calories']
        user['logged_calories'] += calories
        await message.answer(f"Записано: {calories:.1f} ккал.")
        user.pop('food_calories', None)
    except:
        pass

@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message):
    user = users.get(message.chat.id)
    if not user:
        await message.answer("Сначала необходимо настроить профиль.")
        return
    
    try:
        _, workout_type, minutes = message.text.split()
        minutes = int(minutes)
    except:
        await message.answer("Использование: /log_workout бег 30")
        return
    
    calories = minutes * 10
    water_loss = (minutes // 30) * 200
    
    user['burned_calories'] += calories
    user['water_goal'] += water_loss
    
    response = f"Тренировка: {workout_type}, {minutes} минут. Сожжено калорий: {calories}."
    if water_loss > 0:
        response += f" Дополнительно: выпейте {water_loss} мл воды."
    
    await message.answer(response)

@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    user = users.get(message.chat.id)
    if not user:
        await message.answer("Сначала необходимо настроить профиль.")
        return
    
    response = (
        f"Вода:\n"
        f"- Выпито: {user['logged_water']} мл из {user['water_goal']} мл.\n"
        f"- Осталось: {max(user['water_goal'] - user['logged_water'], 0)} мл.\n\n"
        f"Калории:\n"
        f"- Потреблено: {int(user['logged_calories'])} ккал из {user['calorie_goal']} ккал.\n"
        f"- Сожжено: {user['burned_calories']} ккал.\n"
        f"- Баланс: {int(user['logged_calories'] - user['burned_calories'])} ккал."
    )
    
    await message.answer(response)