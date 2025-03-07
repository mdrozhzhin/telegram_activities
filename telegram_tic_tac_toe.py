import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

games = {}


def create_board():
    return [" " for _ in range(9)]


def print_board(board):
    return (
        f"{board[0]} | {board[1]} | {board[2]}\n"
        "---------\n"
        f"{board[3]} | {board[4]} | {board[5]}\n"
        "---------\n"
        f"{board[6]} | {board[7]} | {board[8]}"
    )


def check_winner(board):
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]  # diagonals
    ]

    for a, b, c in lines:
        if board[a] == board[b] == board[c] != " ":
            return board[a]

    if " " not in board:
        return "draw"

    return None


def bot_move(board):
    empty = [i for i, cell in enumerate(board) if cell == " "]
    return random.choice(empty) if empty else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🎮 Начать игру", callback_data="menu_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "❌⭕ Добро пожаловать в игру Крестики-нолики!",
        reply_markup=reply_markup
    )

def get_menu_buttons(game_active=False):
    buttons = []
    if game_active:
        buttons.append([
            InlineKeyboardButton("🔄 Заново", callback_data="menu_restart"),
            InlineKeyboardButton("🚪 Закрыть", callback_data="menu_close")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🎮 Начать игру", callback_data="menu_start")
        ])
    return InlineKeyboardMarkup(buttons)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global text
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    data = query.data

    # Menu processing
    if data.startswith("menu_"):
        if data == "menu_start":
            keyboard = [
                [
                    InlineKeyboardButton("👥 Против человека", callback_data="mode_human"),
                    InlineKeyboardButton("🤖 Против бота", callback_data="mode_bot")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Выберите режим игры:",
                reply_markup=reply_markup
            )
            return

        elif data == "menu_restart":
            # Full game restart
            games.pop(chat_id, None)
            keyboard = [
                [
                    InlineKeyboardButton("👥 Против человека", callback_data="mode_human"),
                    InlineKeyboardButton("🤖 Против бота", callback_data="mode_bot")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🔄 Новая игра! Выберите режим:",
                reply_markup=reply_markup
            )
            return

        elif data == "menu_close":
            games.pop(chat_id, None)
            await query.edit_message_text(
                "❌ Игра завершена",
                reply_markup=get_menu_buttons(game_active=False)
            )
            return

    if not query.message:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Игровое сообщение не найдено. Начните новую игру через /start"
        )
        return

    if data.startswith("mode_"):
        mode = data.split("_")[1]
        games[chat_id] = {"mode": mode}

        if mode == "bot":
            keyboard = [
                [
                    InlineKeyboardButton("❌ X", callback_data="symbol_X"),
                    InlineKeyboardButton("⭕ O", callback_data="symbol_O")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Выберите ваш символ:", reply_markup=reply_markup)
        else:
            games[chat_id].update({
                "board": create_board(),
                "current_player": "X",
                "game_over": False
            })
            keyboard = [[InlineKeyboardButton(" ", callback_data=str(i + j)) for j in range(3)] for i in range(0, 9, 3)]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Новая игра! Ходят крестики (X)", reply_markup=reply_markup)

    elif data.startswith("symbol_"):
        symbol = data.split("_")[1]
        games[chat_id].update({
            "player_symbol": symbol,
            "current_player": "X",
            "board": create_board(),
            "game_over": False
        })

        if symbol == "O":
            bot_position = bot_move(games[chat_id]["board"])
            games[chat_id]["board"][bot_position] = "X"
            games[chat_id]["current_player"] = "O"

        keyboard = [[InlineKeyboardButton(cell, callback_data=str(i + j)) for j, cell in
                     enumerate(games[chat_id]["board"][i:i + 3])] for i in range(0, 9, 3)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Ваш ход (⭕)" if symbol == "O" else "Ходят: ❌"
        await query.edit_message_text(text, reply_markup=reply_markup)


    else:
        # Player's move processing
        if chat_id not in games:
            await query.edit_message_text("Игра не найдена. Введите /start чтобы начать")
            return

        game = games[chat_id]

        if game["mode"] == "bot" and game["current_player"] != game["player_symbol"]:
            await query.answer("⏳ Сейчас ходит бот!")
            return

        if game.get("game_over"):
            await query.answer("Игра уже завершена!")
            return

        try:
            position = int(data)
        except ValueError:
            return

        if game["board"][position] != " ":
            await query.answer("Клетка уже занята!")
            return

        current_symbol = game["current_player"]
        game["board"][position] = current_symbol
        winner = check_winner(game["board"])

        if winner:
            game["game_over"] = True
            if winner == "draw":
                text = "Ничья! 🟨"
            else:
                text = f"Победитель: {'❌' if winner == 'X' else '⭕'}!"
        else:

            if game["mode"] == "human":

                game["current_player"] = 'O' if current_symbol == 'X' else 'X'
                text = f"Ходят: {'❌' if game['current_player'] == 'X' else '⭕'}"

            elif game["mode"] == "bot":

                game["current_player"] = 'O' if current_symbol == 'X' else 'X'

                bot_symbol = 'X' if game["player_symbol"] == 'O' else 'O'
                bot_position = bot_move(game["board"])
                if bot_position is not None:
                    game["board"][bot_position] = bot_symbol
                    winner = check_winner(game["board"])
                    if winner:
                        game["game_over"] = True
                        text = "Победил бот! 🤖" if winner == bot_symbol else "Ничья! 🟨"
                    else:
                        game["current_player"] = game["player_symbol"]
                        text = f"Ваш ход ({game['player_symbol']})"

        game_board_keyboard = [
            [
                InlineKeyboardButton(cell, callback_data=str(i + j))
                for j, cell in enumerate(game["board"][i:i + 3])
            ]
            for i in range(0, 9, 3)
        ]

        reply_markup = InlineKeyboardMarkup([
            *game_board_keyboard,
            *get_menu_buttons(game_active=True).inline_keyboard
        ])

        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error updating message: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❌⭕ Помощь по игре:\n\n"
        "🎮 Начать игру - запускает новую игру\n"
        "🔄 Заново - начинает новую игру заново\n"
        "🚪 Закрыть - завершает текущую игру\n\n"
        "Используйте кнопки меню под игровым полем для управления!"
    )


def main() -> None:
    application = Application.builder().token("").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_click))

    application.run_polling()


if __name__ == "__main__":
    main()
