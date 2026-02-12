# -*- coding: utf-8 -*-

"""
    ╔══════════════════════════════════╗
    ║  QR Code Generator & Scanner     ║
    ║  by @your_username               ║
    ╚══════════════════════════════════╝
"""

# meta developer: @your_username
# requires: qrcode pillow pyzbar

__version__ = (1, 1, 0)

import io
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
from .. import loader, utils
from telethon.tl.types import Message, DocumentAttributeFilename


@loader.tds
class QRCodeMod(loader.Module):
    """Генератор и сканер QR кодов"""

    strings = {
        "name": "QRCode",
        "no_text": "<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи текст для QR кода!</b>\n<code>.qr [текст]</code>",
        "no_reply": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ответь на изображение с QR кодом!</b>",
        "generating": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Генерирую QR код...</b>",
        "scanning": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Сканирую QR код...</b>",
        "not_found": "<emoji document_id=5210952531676504517>❌</emoji> <b>QR код не найден на изображении</b>",
        "wifi_help": "<emoji document_id=5210952531676504517>❌</emoji> <b>Формат WiFi QR:</b>\n<code>.qrwifi [SSID] [пароль] [тип]</code>\n<i>Тип: WPA, WEP, или пусто</i>",
    }

    strings_ru = strings

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "fill_color",
                "black",
                lambda: "Цвет QR кода (black, white, red, blue, green)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "back_color",
                "white",
                lambda: "Цвет фона (black, white, red, blue, green)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "auto_scan",
                True,
                lambda: "Автоматически сканировать QR коды в группе",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "allowed_chat_id",
                -1002231218862,
                lambda: "ID чата для автосканирования",
                validator=loader.validators.Integer(),
            ),
        )

    async def scan_qr_from_photo(self, photo_bytes: bytes) -> list:
        """Сканирование QR кода из фото"""
        try:
            img = Image.open(io.BytesIO(photo_bytes))
            decoded = decode(img)
            return decoded
        except Exception as e:
            return []

    @loader.command(ru_doc="<текст> - Создать QR код")
    async def qr(self, message: Message):
        """<text> - Generate QR code"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings["no_text"])
            return

        await utils.answer(message, self.strings["generating"])

        try:
            # Создание QR кода
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(args)
            qr.make(fit=True)

            img = qr.make_image(
                fill_color=self.config["fill_color"],
                back_color=self.config["back_color"]
            )

            # Сохранение в буфер
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Отправка
            await message.client.send_file(
                message.peer_id,
                buffer,
                caption=f"<emoji document_id=5431815452437257407>📱</emoji> <b>QR код создан</b>\n<code>{args[:100]}</code>",
                reply_to=message.reply_to_msg_id,
            )
            await message.delete()

        except Exception as e:
            await utils.answer(message, f"<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {e}")

    @loader.command(ru_doc="- Сканировать QR код (ответь на фото)")
    async def qrscan(self, message: Message):
        """- Scan QR code (reply to image)"""
        reply = await message.get_reply_message()

        if not reply or not reply.photo:
            await utils.answer(message, self.strings["no_reply"])
            return

        await utils.answer(message, self.strings["scanning"])

        try:
            # Скачивание изображения
            photo = await reply.download_media(bytes)

            # Сканирование
            decoded = await self.scan_qr_from_photo(photo)

            if not decoded:
                await utils.answer(message, self.strings["not_found"])
                return

            # Вывод результатов
            text = "<emoji document_id=5314181343643865367>✅</emoji> <b>QR код распознан:</b>\n\n"

            for i, qr in enumerate(decoded, 1):
                data = qr.data.decode("utf-8")
                qr_type = qr.type
                text += f"<b>#{i}</b> [{qr_type}]\n<code>{data}</code>\n\n"

            await utils.answer(message, text)

        except Exception as e:
            await utils.answer(message, f"<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {e}")

    @loader.watcher(only_messages=True)
    async def qr_watcher(self, message: Message):
        """Автоматическое сканирование QR кодов в определенной группе"""
        # Проверка включена ли функция
        if not self.config["auto_scan"]:
            return

        # Проверка что это нужная группа
        chat_id = utils.get_chat_id(message)
        if chat_id != self.config["allowed_chat_id"]:
            return

        # Проверка что есть фото
        if not message.photo:
            return

        # Проверка что это не наше сообщение
        if message.out:
            return

        try:
            # Скачивание
            photo = await message.download_media(bytes)

            # Сканирование
            decoded = await self.scan_qr_from_photo(photo)

            if decoded:
                # Отправка результата
                text = "<emoji document_id=5314181343643865367>📱</emoji> <b>QR найден:</b>\n\n"

                for i, qr in enumerate(decoded, 1):
                    data = qr.data.decode("utf-8")
                    qr_type = qr.type

                    # Ограничение длины для автосканирования
                    if len(data) > 200:
                        data = data[:200] + "..."

                    text += f"<code>{data}</code>\n"

                text += "\n<i>🤖 Auto QR Scanner</i>"

                await message.reply(text)
        except:
            pass  # Тихо игнорируем ошибки в watcher

    @loader.command(ru_doc="<SSID> <пароль> [тип] - WiFi QR код")
    async def qrwifi(self, message: Message):
        """<SSID> <password> [type] - Generate WiFi QR code"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings["wifi_help"])
            return

        parts = args.split(maxsplit=2)
        if len(parts) < 2:
            await utils.answer(message, self.strings["wifi_help"])
            return

        ssid = parts[0]
        password = parts[1]
        auth_type = parts[2].upper() if len(parts) > 2 else "WPA"

        # Формат WiFi QR
        wifi_string = f"WIFI:T:{auth_type};S:{ssid};P:{password};;"

        await utils.answer(message, self.strings["generating"])

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(wifi_string)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            await message.client.send_file(
                message.peer_id,
                buffer,
                caption=f"<emoji document_id=5431815452437257407>📱</emoji> <b>WiFi QR код</b>\n\n"
                        f"<b>SSID:</b> <code>{ssid}</code>\n"
                        f"<b>Пароль:</b> <code>{password}</code>\n"
                        f"<b>Тип:</b> {auth_type}",
                reply_to=message.reply_to_msg_id,
            )
            await message.delete()

        except Exception as e:
            await utils.answer(message, f"<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {e}")

    @loader.command(ru_doc="- Переключить автосканирование")
    async def qrtoggle(self, message: Message):
        """- Toggle auto scanning"""
        self.config["auto_scan"] = not self.config["auto_scan"]

        status = "включено" if self.config["auto_scan"] else "выключено"
        emoji = "✅" if self.config["auto_scan"] else "❌"

        await utils.answer(
            message,
            f"<emoji document_id=5314181343643865367>{emoji}</emoji> <b>Автосканирование QR {status}</b>\n\n"
            f"<i>Группа: {self.config['allowed_chat_id']}</i>"
        )
