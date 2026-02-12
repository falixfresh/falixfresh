# -*- coding: utf-8 -*-

"""
    ╔══════════════════════════════════╗
    ║  Voice to Text Converter         ║
    ║  Speech Recognition API          ║
    ╚══════════════════════════════════╝
"""

# meta developer: @your_username
# requires: SpeechRecognition pydub

__version__ = (1, 1, 0)

import io
import os
import speech_recognition as sr
from pydub import AudioSegment
from .. import loader, utils
from telethon.tl.types import Message


@loader.tds
class VoiceToTextMod(loader.Module):
    """Преобразование голосовых сообщений в текст"""

    strings = {
        "name": "VoiceToText",
        "no_reply": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ответь на голосовое сообщение!</b>",
        "processing": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Распознаю речь...</b>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка:</b> {}",
        "no_speech": "<emoji document_id=5210952531676504517>❌</emoji> <b>Речь не распознана</b>\n<i>Попробуй другое аудио</i>",
        "success": "<emoji document_id=5314181343643865367>✅</emoji> <b>Распознанный текст:</b>\n\n{}",
        "wrong_chat": "<emoji document_id=5210952531676504517>❌</emoji> <b>Эта команда работает только в определенной группе!</b>",
    }

    strings_ru = strings

    # ID группы для автораспознавания
    TARGET_CHAT_ID = -1002231218862

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "language",
                "ru-RU",
                lambda: "Язык распознавания (ru-RU, en-US, de-DE, fr-FR)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "api_service",
                "google",
                lambda: "API сервис (google, sphinx)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "auto_recognize",
                True,
                lambda: "Автоматически распознавать все войсы в группе",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "allowed_chat_id",
                -1002231218862,
                lambda: "ID чата для автораспознавания",
                validator=loader.validators.Integer(),
            ),
        )
        self.recognizer = sr.Recognizer()

    async def convert_to_wav(self, audio_data: bytes, source_format: str = "ogg") -> bytes:
        """Конвертация аудио в WAV"""
        try:
            audio = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=source_format
            )

            # Конвертация в моно, 16kHz
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)

            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_buffer.seek(0)

            return wav_buffer.read()
        except Exception as e:
            raise Exception(f"Ошибка конвертации: {e}")

    async def recognize_voice(self, voice_data: bytes, duration: int) -> tuple:
        """Распознавание голоса, возвращает (текст, ошибка)"""
        try:
            # Конвертация в WAV
            wav_data = await self.convert_to_wav(voice_data)

            # Распознавание
            with sr.AudioFile(io.BytesIO(wav_data)) as source:
                audio = self.recognizer.record(source)

            # Выбор API
            if self.config["api_service"] == "google":
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.config["language"]
                )
            else:
                text = self.recognizer.recognize_sphinx(audio)

            return (text, None)

        except sr.UnknownValueError:
            return (None, "no_speech")
        except sr.RequestError as e:
            return (None, f"API недоступен: {e}")
        except Exception as e:
            return (None, str(e))

    @loader.command(ru_doc="- Распознать голосовое сообщение")
    async def vtt(self, message: Message):
        """- Convert voice message to text"""
        reply = await message.get_reply_message()

        if not reply or not reply.voice:
            await utils.answer(message, self.strings["no_reply"])
            return

        await utils.answer(message, self.strings["processing"])

        try:
            # Скачивание голосового сообщения
            voice_data = await reply.download_media(bytes)
            duration = reply.voice.duration

            # Распознавание
            text, error = await self.recognize_voice(voice_data, duration)

            if error:
                if error == "no_speech":
                    await utils.answer(message, self.strings["no_speech"])
                else:
                    await utils.answer(message, self.strings["error"].format(error))
                return

            # Форматирование вывода
            output = self.strings["success"].format(f"<code>{text}</code>")
            output += f"\n\n<i>⏱ Длительность: {duration}с</i>"

            await utils.answer(message, output)

        except Exception as e:
            await utils.answer(message, self.strings["error"].format(str(e)))

    @loader.watcher(only_messages=True)
    async def voice_watcher(self, message: Message):
        """Автоматическое распознавание войсов в определенной группе"""
        # Проверка включена ли функция
        if not self.config["auto_recognize"]:
            return

        # Проверка что это нужная группа
        chat_id = utils.get_chat_id(message)
        if chat_id != self.config["allowed_chat_id"]:
            return

        # Проверка что это голосовое сообщение
        if not message.voice:
            return

        # Проверка что это не наше сообщение
        if message.out:
            return

        try:
            # Скачивание
            voice_data = await message.download_media(bytes)
            duration = message.voice.duration

            # Распознавание
            text, error = await self.recognize_voice(voice_data, duration)

            if text:
                # Отправка распознанного текста
                await message.reply(
                    f"<emoji document_id=5314181343643865367>🎤</emoji> <b>Распознано:</b>\n\n"
                    f"<code>{text}</code>\n\n"
                    f"<i>⏱ {duration}с | 🤖 Auto VTT</i>"
                )
        except:
            pass  # Тихо игнорируем ошибки в watcher

    @loader.command(ru_doc="<язык> - Установить язык распознавания")
    async def vttlang(self, message: Message):
        """<lang> - Set recognition language"""
        args = utils.get_args_raw(message)

        languages = {
            "ru": "ru-RU",
            "en": "en-US",
            "de": "de-DE",
            "fr": "fr-FR",
            "es": "es-ES",
            "it": "it-IT",
            "pt": "pt-PT",
            "uk": "uk-UA",
        }

        if not args:
            langs_text = "<b>🎤 Доступные языки:</b>\n\n"
            for code, full in languages.items():
                langs_text += f"<code>{code}</code> - {full}\n"
            langs_text += "\n<i>Используй: .vttlang [код]</i>"
            await utils.answer(message, langs_text)
            return

        if args in languages:
            self.config["language"] = languages[args]
            await utils.answer(
                message,
                f"<emoji document_id=5314181343643865367>✅</emoji> <b>Язык установлен:</b> {languages[args]}"
            )
        else:
            await utils.answer(
                message,
                f"<emoji document_id=5210952531676504517>❌</emoji> <b>Неверный код языка!</b>\n"
                f"<i>Используй .vttlang без аргументов для списка</i>"
            )

    @loader.command(ru_doc="- Переключить автораспознавание")
    async def vtttoggle(self, message: Message):
        """- Toggle auto recognition"""
        self.config["auto_recognize"] = not self.config["auto_recognize"]

        status = "включено" if self.config["auto_recognize"] else "выключено"
        emoji = "✅" if self.config["auto_recognize"] else "❌"

        await utils.answer(
            message,
            f"<emoji document_id=5314181343643865367>{emoji}</emoji> <b>Автораспознавание {status}</b>\n\n"
            f"<i>Группа: {self.config['allowed_chat_id']}</i>"
        )
