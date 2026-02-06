from .api import get_weather


def calculate_calorie_goal(user):
    """Рассчитывает норму калорий"""
    bmr = 10 * user["weight"] + 6.25 * user["height"] - 5 * user["age"]
    activity_bonus = 300 if user["activity"] >= 30 else 150
    return int(bmr + activity_bonus)


def calculate_water_goal(user, temperature):
    """Рассчитывает дневную норму воды"""
    base = user['weight'] * 30
    activity_bonus = (user['activity'] // 30) * 500
    weather_bonus = 500 if temperature > 25 else 0

    return base + activity_bonus + weather_bonus



