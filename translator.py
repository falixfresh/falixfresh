# -*- coding: utf-8 -*-

"""
    ╔══════════════════════════════════╗
    ║  Translator Module               ║
    ║  Google Translate API            ║
    ╚══════════════════════════════════╝
"""

# meta developer: @your_username
# requires: deep-translator googletrans==4.0.0rc1

__version__ = (1, 0, 0)

import io
from deep_translator import GoogleTranslator
from googletrans import Translator, LANGUAGES
from .. import loader, utils
from telethon.tl.types import Message


@loader.tds
class TranslatorMod(loader.Module):
    """Переводчик с автоопределением языка"""

    strings = {
        "name": "Translator",
        "no_text": "<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи текст для перевода!</b>\n<code>.tr [текст]</code>",
        "translating": "<emoji document_id=5451646226975955576>⌛</emoji> <b>Перевожу...</b>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка перевода:</b> {}",
        "lang_help": "<b>🌐 Доступные языки:</b>\n\n{}\n\n<i>Используй: .tr en [текст]</i>",
    }

    strings_ru = strings

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "default_lang",
                "ru",
                lambda: "Язык перевода по умолчанию (en, ru, de, fr, es)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "show_original",
                True,
                lambda: "Показывать оригинальный текст",
                validator=loader.validators.Boolean(),
            ),
        )
        self.translator = None

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.translator = Translator()

    def get_flag(self, lang_code: str) -> str:
        """Получить флаг для языка"""
        flags = {
            "en": "🇬🇧", "ru": "🇷🇺", "de": "🇩🇪", "fr": "🇫🇷",
            "es": "🇪🇸", "it": "🇮🇹", "pt": "🇵🇹", "pl": "🇵🇱",
            "uk": "🇺🇦", "ja": "🇯🇵", "zh-cn": "🇨🇳", "ko": "🇰🇷",
            "ar": "🇸🇦", "tr": "🇹🇷", "hi": "🇮🇳", "th": "🇹🇭",
            "vi": "🇻🇳", "nl": "🇳🇱", "sv": "🇸🇪", "no": "🇳🇴",
            "da": "🇩🇰", "fi": "🇫🇮", "cs": "🇨🇿", "el": "🇬🇷",
            "he": "🇮🇱", "id": "🇮🇩", "ms": "🇲🇾", "ro": "🇷🇴",
        }
        return flags.get(lang_code, "🌐")

    @loader.command(ru_doc="[язык] <текст> - Перевести текст")
    async def tr(self, message: Message):
        """[lang] <text> - Translate text"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        # Получение текста
        if not args and reply:
            text = reply.raw_text
            target_lang = self.config["default_lang"]
        elif args:
            parts = args.split(maxsplit=1)
            if len(parts) == 2 and parts[0] in LANGUAGES:
                target_lang = parts[0]
                text = parts[1]
            else:
                target_lang = self.config["default_lang"]
                text = args
        else:
            await utils.answer(message, self.strings["no_text"])
            return

        await utils.answer(message, self.strings["translating"])

        try:
            # Определение исходного языка
            detected = self.translator.detect(text)
            source_lang = detected.lang

            # Если язык совпадает с целевым, меняем на английский
            if source_lang == target_lang:
                target_lang = "en" if target_lang != "en" else "ru"

            # Перевод
            result = self.translator.translate(text, src=source_lang, dest=target_lang)

            # Форматирование
            source_flag = self.get_flag(source_lang)
            target_flag = self.get_flag(target_lang)

            output = f"<b>{source_flag} {LANGUAGES.get(source_lang, source_lang).title()}</b> → "
            output += f"<b>{target_flag} {LANGUAGES.get(target_lang, target_lang).title()}</b>\n\n"

            if self.config["show_original"] and len(text) < 200:
                output += f"<i>{text}</i>\n\n"

            output += f"<b>{result.text}</b>"

            # Если есть транскрипция
            if result.pronunciation and result.pronunciation != result.text:
                output += f"\n\n<i>🔊 {result.pronunciation}</i>"

            await utils.answer(message, output)

        except Exception as e:
            await utils.answer(message, self.strings["error"].format(str(e)))

    @loader.command(ru_doc="- Показать доступные языки")
    async def langs(self, message: Message):
        """- Show available languages"""
        langs_text = ""

        # Популярные языки
        popular = ["en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk", "ja", "zh-cn", "ko", "ar", "tr"]

        langs_text += "<b>Популярные:</b>\n"
        for code in popular:
            flag = self.get_flag(code)
            name = LANGUAGES.get(code, code)
            langs_text += f"{flag} <code>{code}</code> - {name.title()}\n"

        langs_text += f"\n<i>Всего доступно {len(LANGUAGES)} языков</i>"

        await utils.answer(message, self.strings["lang_help"].format(langs_text))

    @loader.command(ru_doc="<язык> - Установить язык по умолчанию")
    async def setlang(self, message: Message):
        """<lang> - Set default language"""
        args = utils.get_args_raw(message)

        if not args or args not in LANGUAGES:
            await utils.answer(
                message,
                f"<emoji document_id=5210952531676504517>❌</emoji> <b>Неверный код языка!</b>\n"
                f"<i>Используй .langs для списка</i>"
            )
            return

        self.config["default_lang"] = args
        flag = self.get_flag(args)
        lang_name = LANGUAGES.get(args, args)

        await utils.answer(
            message,
            f"<emoji document_id=5314181343643865367>✅</emoji> <b>Язык по умолчанию:</b>\n"
            f"{flag} {lang_name.title()} (<code>{args}</code>)"
        )
