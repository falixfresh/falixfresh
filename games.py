# -*- coding: utf-8 -*-

"""
    ╔══════════════════════════════════╗
    ║  Mini Games Collection           ║
    ║  Fun games for Hikka             ║
    ╚══════════════════════════════════╝
"""

# meta developer: @your_username

__version__ = (1, 0, 0)

import random
import asyncio
from .. import loader, utils
from telethon.tl.types import Message


@loader.tds
class GamesMod(loader.Module):
    """Мини-игры для развлечения"""

    strings = {
        "name": "Games",
    }

    def __init__(self):
        self.ttt_games = {}  # Tic-tac-toe games
        self.rps_waiting = {}  # Rock-paper-scissors waiting

    @loader.command(ru_doc="- Бросить кубик")
    async def dice(self, message: Message):
        """- Roll a dice"""
        result = random.randint(1, 6)
        dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

        await utils.answer(
            message,
            f"<emoji document_id=5188311512791393083>🎲</emoji> <b>Бросок кубика:</b>\n\n"
            f"<b>{dice_emoji[result-1]} {result}</b>"
        )

    @loader.command(ru_doc="- Подбросить монетку")
    async def coin(self, message: Message):
        """- Flip a coin"""
        result = random.choice(["Орел", "Решка"])
        emoji = "🪙" if result == "Орел" else "💿"

        await utils.answer(
            message,
            f"<emoji document_id=5188311512791393083>🪙</emoji> <b>Подброс монетки:</b>\n\n"
            f"{emoji} <b>{result}!</b>"
        )

    @loader.command(ru_doc="[мин] [макс] - Случайное число")
    async def rand(self, message: Message):
        """[min] [max] - Random number"""
        args = utils.get_args_raw(message)

        try:
            if args:
                parts = args.split()
                if len(parts) == 2:
                    min_val, max_val = int(parts[0]), int(parts[1])
                else:
                    min_val, max_val = 1, int(parts[0])
            else:
                min_val, max_val = 1, 100

            result = random.randint(min_val, max_val)

            await utils.answer(
                message,
                f"<emoji document_id=5188311512791393083>🎰</emoji> <b>Случайное число</b>\n"
                f"<i>[{min_val} - {max_val}]</i>\n\n"
                f"<b>Результат: {result}</b>"
            )
        except:
            await utils.answer(
                message,
                "<emoji document_id=5210952531676504517>❌</emoji> <b>Неверный формат!</b>\n"
                "<code>.rand [макс]</code> или <code>.rand [мин] [макс]</code>"
            )

    @loader.command(ru_doc="<варианты через |> - Выбрать случайно")
    async def choose(self, message: Message):
        """<options with |> - Choose randomly"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(
                message,
                "<emoji document_id=5210952531676504517>❌</emoji> <b>Укажи варианты!</b>\n"
                "<code>.choose пицца | суши | бургер</code>"
            )
            return

        options = [opt.strip() for opt in args.split("|")]
        choice = random.choice(options)

        await utils.answer(
            message,
            f"<emoji document_id=5188311512791393083>🎯</emoji> <b>Я выбираю:</b>\n\n"
            f"<b>→ {choice}</b>\n\n"
            f"<i>Из {len(options)} вариантов</i>"
        )

    @loader.command(ru_doc="- Камень, ножницы, бумага")
    async def rps(self, message: Message):
        """- Rock, Paper, Scissors"""
        choices = {
            "🪨": "Камень",
            "✂️": "Ножницы", 
            "📄": "Бумага"
        }

        user_choice = random.choice(list(choices.keys()))
        bot_choice = random.choice(list(choices.keys()))

        # Определение победителя
        wins = {
            "🪨": "✂️",  # Камень бьет ножницы
            "✂️": "📄",  # Ножницы бьют бумагу
            "📄": "🪨"   # Бумага бьет камень
        }

        if user_choice == bot_choice:
            result = "🤝 <b>Ничья!</b>"
        elif wins[user_choice] == bot_choice:
            result = "🎉 <b>Ты победил!</b>"
        else:
            result = "😔 <b>Я победил!</b>"

        await utils.answer(
            message,
            f"<emoji document_id=5188311512791393083>✊</emoji> <b>Камень, ножницы, бумага!</b>\n\n"
            f"<b>Ты:</b> {user_choice} {choices[user_choice]}\n"
            f"<b>Я:</b> {bot_choice} {choices[bot_choice]}\n\n"
            f"{result}"
        )

    @loader.command(ru_doc="<число> - Угадай число (1-100)")
    async def guess(self, message: Message):
        """<number> - Guess the number (1-100)"""
        if not hasattr(self, "_guess_number"):
            self._guess_number = random.randint(1, 100)
            self._guess_attempts = 0

        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(
                message,
                f"<emoji document_id=5188311512791393083>🎮</emoji> <b>Угадай число от 1 до 100!</b>\n\n"
                f"<i>Попытка #{self._guess_attempts + 1}</i>\n"
                f"<code>.guess [число]</code>"
            )
            return

        try:
            guess = int(args)
            self._guess_attempts += 1

            if guess == self._guess_number:
                await utils.answer(
                    message,
                    f"<emoji document_id=5314181343643865367>🎉</emoji> <b>Поздравляю!</b>\n\n"
                    f"Ты угадал число <b>{self._guess_number}</b>\n"
                    f"за <b>{self._guess_attempts}</b> попыток!\n\n"
                    f"<i>Начинаю новую игру...</i>"
                )
                delattr(self, "_guess_number")
                delattr(self, "_guess_attempts")
            elif guess < self._guess_number:
                await utils.answer(
                    message,
                    f"<emoji document_id=5188311512791393083>📈</emoji> <b>Больше!</b>\n\n"
                    f"Твоё число: <b>{guess}</b>\n"
                    f"Попытка #{self._guess_attempts}"
                )
            else:
                await utils.answer(
                    message,
                    f"<emoji document_id=5188311512791393083>📉</emoji> <b>Меньше!</b>\n\n"
                    f"Твоё число: <b>{guess}</b>\n"
                    f"Попытка #{self._guess_attempts}"
                )
        except:
            await utils.answer(
                message,
                "<emoji document_id=5210952531676504517>❌</emoji> <b>Введи число от 1 до 100!</b>"
            )

    @loader.command(ru_doc="- Колесо фортуны")
    async def spin(self, message: Message):
        """- Spin the wheel"""
        prizes = [
            ("💎", "Джекпот!", 1),
            ("🎁", "Супер приз!", 5),
            ("⭐", "Приз!", 15),
            ("🎈", "Повезло!", 25),
            ("😐", "Ничего", 30),
            ("💩", "Неудача", 24),
        ]

        # Взвешенный выбор
        items, names, weights = zip(*prizes)
        result = random.choices(list(zip(items, names)), weights=weights)[0]

        # Анимация вращения
        msg = await utils.answer(message, "<b>🎰 Вращаю колесо...</b>")

        spin_items = ["🎰", "🎲", "🎯", "🎪", "🎨", "🎭"]
        for i in range(8):
            await asyncio.sleep(0.3)
            await msg.edit(f"<b>{random.choice(spin_items)} Вращаю...</b>")

        await msg.edit(
            f"<emoji document_id=5188311512791393083>🎰</emoji> <b>Колесо фортуны</b>\n\n"
            f"<b>{result[0]} {result[1]}</b>"
        )

    @loader.command(ru_doc="- Генератор оправданий")
    async def excuse(self, message: Message):
        """- Generate excuse"""
        subjects = ["Кот", "Собака", "Интернет", "Компьютер", "Телефон", "Будильник", "Погода"]
        actions = ["сломался", "завис", "пропал", "не работал", "отключился", "глючил"]
        reasons = ["из-за обновления", "внезапно", "без причины", "в самый неподходящий момент", "как назло"]

        excuse = f"{random.choice(subjects)} {random.choice(actions)} {random.choice(reasons)}"

        await utils.answer(
            message,
            f"<emoji document_id=5188311512791393083>🎭</emoji> <b>Твоё оправдание:</b>\n\n"
            f"<i>«{excuse}»</i>"
        )
