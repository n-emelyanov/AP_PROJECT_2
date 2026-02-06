import aiohttp
from models.config import Settings


async def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get("products", [])
                    if products:
                        first_product = products[0]
                        return {
                            "name": first_product.get("product_name", "Неизвестно"),
                            "calories": first_product.get("nutriments", {}).get(
                                "energy-kcal_100g", 0
                            ),
                        }
                    return None
                else:
                    print(f'Ошибка HTTP: {response.status}')
                    return None
        except Exception as e:
            print(f"Ошибка при запросе: {e}")
            return None



async def get_weather(city):
    """Простая асинхронная функция получения погоды"""
    if not Settings().OPEN_WEATHER_TOKEN:
        raise ValueError("Переменная окружения OPEN_WEATHER_TOKEN не установлена!")

    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': Settings().OPEN_WEATHER_TOKEN,
        'units': 'metric',
        'lang': 'ru',
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['main']['temp']
                else:
                    print(f'Ошибка HTTP: {response.status}')
                    return None
                    
    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return None