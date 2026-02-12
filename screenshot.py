# -*- coding: utf-8 -*-

"""
    ╔══════════════════════════════════╗
    ║  Website Screenshot Module       ║
    ║  Preview any website             ║
    ╚══════════════════════════════════╝
"""

# meta developer: @your_username
# requires: selenium webdriver-manager pillow

__version__ = (1, 0, 0)

import io
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from .. import loader, utils
from telethon.tl.types import Message


@loader.tds
class ScreenshotMod(loader.Module):
    """Скриншоты веб-сайтов"""

    strings = {
        "name": "Screenshot",
        "no_url": "<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи URL!</b>\n<code>.screenshot [url]</code>",
        "invalid_url": "<emoji document_id=5210952531676504517>❌</emoji> <b>Неверный URL!</b>\n<i>Добавь http:// или https://</i>",
        "processing": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Делаю скриншот...</b>\n<i>{}</i>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {}",
    }

    strings_ru = strings

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "width",
                1920,
                lambda: "Ширина скриншота",
                validator=loader.validators.Integer(minimum=800),
            ),
            loader.ConfigValue(
                "height",
                1080,
                lambda: "Высота скриншота",
                validator=loader.validators.Integer(minimum=600),
            ),
            loader.ConfigValue(
                "full_page",
                False,
                lambda: "Скриншот всей страницы",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "mobile",
                False,
                lambda: "Мобильная версия сайта",
                validator=loader.validators.Boolean(),
            ),
        )
        self.driver = None

    def validate_url(self, url: str) -> str:
        """Валидация и нормализация URL"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Простая проверка формата URL
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not pattern.match(url):
            return None

        return url

    async def get_driver(self):
        """Инициализация WebDriver"""
        if self.driver:
            return self.driver

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={self.config['width']},{self.config['height']}")

        if self.config["mobile"]:
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return self.driver
        except Exception as e:
            raise Exception(f"Не удалось запустить браузер: {e}")

    @loader.command(ru_doc="<url> - Сделать скриншот сайта")
    async def screenshot(self, message: Message):
        """<url> - Take website screenshot"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings["no_url"])
            return

        # Валидация URL
        url = self.validate_url(args)
        if not url:
            await utils.answer(message, self.strings["invalid_url"])
            return

        await utils.answer(message, self.strings["processing"].format(url))

        try:
            # Получение драйвера
            driver = await self.get_driver()

            # Загрузка страницы
            driver.get(url)

            # Ждем загрузки
            import time
            time.sleep(3)

            # Скриншот
            if self.config["full_page"]:
                # Получаем полную высоту страницы
                total_height = driver.execute_script("return document.body.scrollHeight")
                driver.set_window_size(self.config["width"], total_height)
                time.sleep(1)

            screenshot = driver.get_screenshot_as_png()

            # Оптимизация изображения
            img = Image.open(io.BytesIO(screenshot))

            # Сжатие если слишком большое
            if img.size[1] > 10000:
                ratio = 10000 / img.size[1]
                new_size = (int(img.size[0] * ratio), 10000)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Сохранение
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)

            # Отправка
            await message.client.send_file(
                message.peer_id,
                buffer,
                caption=f"<emoji document_id=5188311512791393083>🌐</emoji> <b>Screenshot</b>\n\n"
                        f"<b>URL:</b> <code>{url}</code>\n"
                        f"<b>Размер:</b> {img.size[0]}x{img.size[1]}px",
                reply_to=message.reply_to_msg_id,
            )
            await message.delete()

        except Exception as e:
            await utils.answer(message, self.strings["error"].format(str(e)))

    @loader.command(ru_doc="<url> - Скриншот мобильной версии")
    async def mscreenshot(self, message: Message):
        """<url> - Mobile screenshot"""
        self.config["mobile"] = True
        self.config["width"] = 375
        self.config["height"] = 812

        await self.screenshot(message)

        # Возврат настроек
        self.config["mobile"] = False
        self.config["width"] = 1920
        self.config["height"] = 1080

    @loader.command(ru_doc="<url> - Полный скриншот страницы")
    async def fullshot(self, message: Message):
        """<url> - Full page screenshot"""
        self.config["full_page"] = True
        await self.screenshot(message)
        self.config["full_page"] = False

    async def on_unload(self):
        """Очистка при выгрузке модуля"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
