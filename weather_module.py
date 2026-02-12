# -*- coding: utf-8 -*-

"""
    ╔══════════════════════════════════╗
    ║  Weather Module for Hikka        ║
    ║  by @your_username               ║
    ║  API: Open-Meteo (free)          ║
    ╚══════════════════════════════════╝
"""

# meta developer: @your_username
# meta banner: https://i.imgur.com/weather.jpg

__version__ = (1, 0, 0)

import aiohttp
from datetime import datetime
from .. import loader, utils
from telethon.tl.types import Message


@loader.tds
class WeatherMod(loader.Module):
    """Модуль погоды через Open-Meteo API"""

    strings = {
        "name": "Weather",
        "no_city": "<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи город!</b>\n<code>.weather [город]</code>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {}",
        "searching": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Ищу погоду...</b>",
        "not_found": "<emoji document_id=5210952531676504517>❌</emoji> <b>Город не найден</b>",
    }

    strings_ru = {
        "no_city": "<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи город!</b>\n<code>.weather [город]</code>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {}",
        "searching": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Ищу погоду...</b>",
        "not_found": "<emoji document_id=5210952531676504517>❌</emoji> <b>Город не найден</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "default_city",
                None,
                lambda: "Город по умолчанию",
                validator=loader.validators.String(),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    def get_weather_emoji(self, code: int, is_day: bool) -> str:
        """Получить эмодзи для погодного кода WMO"""
        weather_codes = {
            0: "☀️" if is_day else "🌙",  # Clear
            1: "🌤️" if is_day else "🌙",  # Mainly clear
            2: "⛅" if is_day else "☁️",  # Partly cloudy
            3: "☁️",  # Overcast
            45: "🌫️",  # Fog
            48: "🌫️",  # Depositing rime fog
            51: "🌦️",  # Light drizzle
            53: "🌧️",  # Moderate drizzle
            55: "🌧️",  # Dense drizzle
            61: "🌧️",  # Slight rain
            63: "🌧️",  # Moderate rain
            65: "🌧️",  # Heavy rain
            71: "🌨️",  # Slight snow
            73: "🌨️",  # Moderate snow
            75: "🌨️",  # Heavy snow
            77: "🌨️",  # Snow grains
            80: "🌦️",  # Slight rain showers
            81: "🌧️",  # Moderate rain showers
            82: "⛈️",  # Violent rain showers
            85: "🌨️",  # Slight snow showers
            86: "🌨️",  # Heavy snow showers
            95: "⛈️",  # Thunderstorm
            96: "⛈️",  # Thunderstorm with hail
            99: "⛈️",  # Thunderstorm with heavy hail
        }
        return weather_codes.get(code, "🌡️")

    def get_weather_desc(self, code: int) -> str:
        """Получить описание погоды"""
        descriptions = {
            0: "Ясно",
            1: "В основном ясно",
            2: "Переменная облачность",
            3: "Пасмурно",
            45: "Туман",
            48: "Изморозь",
            51: "Морось",
            53: "Морось",
            55: "Сильная морось",
            61: "Небольшой дождь",
            63: "Дождь",
            65: "Сильный дождь",
            71: "Небольшой снег",
            73: "Снег",
            75: "Сильный снег",
            77: "Снежная крупа",
            80: "Небольшие осадки",
            81: "Ливень",
            82: "Сильный ливень",
            85: "Снегопад",
            86: "Сильный снегопад",
            95: "Гроза",
            96: "Гроза с градом",
            99: "Гроза с крупным градом",
        }
        return descriptions.get(code, "Неизвестно")

    def get_wind_direction(self, degrees: float) -> str:
        """Получить направление ветра"""
        directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
        index = int((degrees + 22.5) / 45) % 8
        return directions[index]

    async def geocode_city(self, city: str) -> tuple:
        """Геокодирование города через Open-Meteo API"""
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": city,
            "count": 1,
            "language": "ru",
            "format": "json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()
                if not data.get("results"):
                    return None

                result = data["results"][0]
                return (
                    result["latitude"],
                    result["longitude"],
                    result["name"],
                    result.get("country", ""),
                )

    async def get_weather(self, lat: float, lon: float) -> dict:
        """Получить погоду через Open-Meteo API"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,is_day",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto",
            "forecast_days": 3
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()

    @loader.command(ru_doc="[город] - Показать погоду")
    async def weather(self, message: Message):
        """[city] - Get weather forecast"""
        args = utils.get_args_raw(message)

        if not args:
            if self.config["default_city"]:
                args = self.config["default_city"]
            else:
                await utils.answer(message, self.strings["no_city"])
                return

        await utils.answer(message, self.strings["searching"])

        # Геокодирование
        geo_result = await self.geocode_city(args)
        if not geo_result:
            await utils.answer(message, self.strings["not_found"])
            return

        lat, lon, city_name, country = geo_result

        # Получение погоды
        weather_data = await self.get_weather(lat, lon)
        if not weather_data:
            await utils.answer(message, self.strings["error"].format("Не удалось получить данные"))
            return

        current = weather_data["current"]
        daily = weather_data["daily"]

        # Текущая погода
        temp = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        humidity = current["relative_humidity_2m"]
        wind_speed = current["wind_speed_10m"]
        wind_dir = current["wind_direction_10m"]
        weather_code = current["weather_code"]
        is_day = current["is_day"]
        precipitation = current.get("precipitation", 0)

        emoji = self.get_weather_emoji(weather_code, is_day)
        desc = self.get_weather_desc(weather_code)
        wind_direction = self.get_wind_direction(wind_dir)

        # Форматирование сообщения
        text = f"""<emoji document_id=5188311512791393083>🌍</emoji> <b>{city_name}, {country}</b>

{emoji} <b>{desc}</b>

<emoji document_id=5452069934089641166>🌡</emoji> <b>Температура:</b> {temp:+.1f}°C
<emoji document_id=5386766919154016047>🤒</emoji> <b>Ощущается:</b> {feels_like:+.1f}°C
<emoji document_id=5431376038628171216>💧</emoji> <b>Влажность:</b> {humidity}%
<emoji document_id=5431815452437257407>💨</emoji> <b>Ветер:</b> {wind_speed:.1f} м/с {wind_direction}"""

        if precipitation > 0:
            text += f"\n<emoji document_id=5240241223632954241>🌧</emoji> <b>Осадки:</b> {precipitation:.1f} мм"

        # Прогноз на 3 дня
        text += "\n\n<b>📅 Прогноз:</b>\n"

        for i in range(3):
            date = datetime.fromisoformat(daily["time"][i])
            day_name = ["Сегодня", "Завтра", "Послезавтра"][i] if i < 3 else date.strftime("%d.%m")

            max_temp = daily["temperature_2m_max"][i]
            min_temp = daily["temperature_2m_min"][i]
            day_code = daily["weather_code"][i]
            day_emoji = self.get_weather_emoji(day_code, True)
            precip = daily["precipitation_sum"][i]

            text += f"\n{day_emoji} <b>{day_name}:</b> {min_temp:+.0f}°C...{max_temp:+.0f}°C"
            if precip > 0:
                text += f" 💧{precip:.0f}мм"

        text += "\n\n<i>📡 Данные: Open-Meteo</i>"

        await utils.answer(message, text)

    @loader.command(ru_doc="[город] - Установить город по умолчанию")
    async def setcity(self, message: Message):
        """[city] - Set default city"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(
                message,
                f"<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи город!</b>\n"
                f"<code>.setcity [город]</code>"
            )
            return

        # Проверка существования города
        geo_result = await self.geocode_city(args)
        if not geo_result:
            await utils.answer(message, self.strings["not_found"])
            return

        _, _, city_name, country = geo_result
        self.config["default_city"] = args

        await utils.answer(
            message,
            f"<emoji document_id=5314181343643865367>✅</emoji> <b>Город по умолчанию установлен:</b>\n"
            f"{city_name}, {country}"
        )
