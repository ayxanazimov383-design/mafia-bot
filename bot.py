import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8696475636:AAFQkVbi3DyWFZGU0glDPPC04yUPaK6Oihk"

players = {}
roles = {}
alive = set()
votes = {}
night_actions = {"kill": None, "heal": None, "check": None}
group_chat_id = None
game_started = False


def alive_keyboard(action):
    buttons = []
    for user_id in alive:
        name = players[user_id]["name"]
        buttons.append([InlineKeyboardButton(name, callback_data=f"{action}:{user_id}")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я работаю ✅\n"
        "Добавь меня в группу и напиши /game"
    )


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, roles, alive, votes, night_actions, group_chat_id, game_started

    group_chat_id = update.effective_chat.id
    players = {}
    roles = {}
    alive = set()
    votes = {}
    night_actions = {"kill": None, "heal": None, "check": None}
    game_started = False

    await update.message.reply_text(
        "🎮 Игра создана!\n"
        "Игроки пишут /join\n"
        "Когда все готовы — /startgame"
    )


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_started:
        await update.message.reply_text("Игра уже началась.")
        return

    user = update.effective_user

    if user.id in players:
        await update.message.reply_text("Ты уже в игре.")
        return

    players[user.id] = {
        "name": user.first_name,
        "username": user.username
    }
    alive.add(user.id)

    await update.message.reply_text(
        f"✅ {user.first_name} присоединился!\n"
        f"Игроков: {len(players)}"
    )


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_started

    if len(players) < 2:
        await update.message.reply_text("❌ Нужно минимум 2 игрока.")
        return

    game_started = True

    player_ids = list(players.keys())
    random.shuffle(player_ids)

    if len(player_ids) == 2:
        role_list = ["мафия", "мирный"]
    elif len(player_ids) == 3:
        role_list = ["мафия", "комиссар", "мирный"]
    else:
        mafia_count = max(1, len(player_ids) // 4)
        role_list = (
            ["мафия"] * mafia_count
            + ["доктор"]
            + ["комиссар"]
            + ["мирный"] * (len(player_ids) - mafia_count - 2)
        )

    random.shuffle(role_list)

    failed = []

    for user_id, role in zip(player_ids, role_list):
        roles[user_id] = role

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎭 Твоя роль: {role}"
            )
        except:
            failed.append(players[user_id]["name"])

    if failed:
        await update.message.reply_text(
            "⚠️ Эти игроки должны открыть бота в личке и написать /start:\n"
            + "\n".join(failed)
        )
        return

    await update.message.reply_text(
        "✅ Игра началась!\n"
        "Роли отправлены в личку."
    )

    await night(update, context)


async def night(update: Update, context: ContextTypes.DEFAULT_TYPE):
    night_actions["kill"] = None
    night_actions["heal"] = None
    night_actions["check"] = None

    await context.bot.send_message(
        chat_id=group_chat_id,
        text="🌙 Ночь началась.\nВсе роли делают выбор в личке."
    )

    for user_id in alive:
        role = roles.get(user_id)

        if role == "мафия":
            await context.bot.send_message(
                chat_id=user_id,
                text="🔪 Кого убить?",
                reply_markup=alive_keyboard("kill")
            )

        elif role == "доктор":
            await context.bot.send_message(
                chat_id=user_id,
                text="💊 Кого лечить?",
                reply_markup=alive_keyboard("heal")
            )

        elif role == "комиссар":
            await context.bot.send_message(
                chat_id=user_id,
                text="🔍 Кого проверить?",
                reply_markup=alive_keyboard("check")
            )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, target = query.data.split(":")
    target_id = int(target)
    user_id = query.from_user.id

    if user_id not in alive:
        await query.edit_message_text("❌ Ты выбыл.")
        return

    if target_id not in alive:
        await query.edit_message_text("❌ Этот игрок уже выбыл.")
        return

    role = roles.get(user_id)

    if action == "kill":
        if role != "мафия":
            await query.edit_message_text("❌ Ты не мафия.")
            return

        night_actions["kill"] = target_id
        await query.edit_message_text(
            f"🔪 Ты выбрал: {players[target_id]['name']}"
        )

    elif action == "heal":
        if role != "доктор":
            await query.edit_message_text("❌ Ты не доктор.")
            return

        night_actions["heal"] = target_id
        await query.edit_message_text(
            f"💊 Ты лечишь: {players[target_id]['name']}"
        )

    elif action == "check":
        if role != "комиссар":
            await query.edit_message_text("❌ Ты не комиссар.")
            return

        checked_role = roles[target_id]
        await query.edit_message_text(
            f"🔍 {players[target_id]['name']} — {checked_role}"
        )


async def nightresults(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kill_id = night_actions["kill"]
    heal_id = night_actions["heal"]

    if kill_id is None:
        await update.message.reply_text("🌙 Ночью никто не погиб.")
    elif kill_id == heal_id:
        await update.message.reply_text("💊 Доктор спас жертву мафии!")
    else:
        alive.discard(kill_id)
        await update.message.reply_text(
            f"☠️ Ночью погиб: {players[kill_id]['name']}"
        )

    await check_win(update, context)


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voter = update.effective_user.id

    if voter not in alive:
        await update.message.reply_text("❌ Ты выбыл и не можешь голосовать.")
        return

    keyboard = alive_keyboard("vote")
    await update.message.reply_text("🗳 Выбери, против кого голосуешь:", reply_markup=keyboard)


async def vote_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not votes:
        await update.message.reply_text("Пока никто не голосовал.")
        return

    count = {}

    for target_id in votes.values():
        count[target_id] = count.get(target_id, 0) + 1

    eliminated = max(count, key=count.get)
    alive.discard(eliminated)

    await update.message.reply_text(
        f"☠️ Казнён: {players[eliminated]['name']}\n"
        f"Его роль была: {roles[eliminated]}"
    )

    votes.clear()

    await check_win(update, context)


async def check_win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mafia_alive = sum(1 for user_id in alive if roles.get(user_id) == "мафия")
    peaceful_alive = sum(1 for user_id in alive if roles.get(user_id) != "мафия")

    if mafia_alive == 0:
        await update.message.reply_text("🎉 Мирные победили!")
        return

    if mafia_alive >= peaceful_alive:
        await update.message.reply_text("💀 Мафия победила!")
        return

    await update.message.reply_text(
        "☀️ День начался!\n"
        "Обсуждайте и голосуйте командой /vote\n"
        "После голосования напишите /results"
    )


async def players_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not players:
        await update.message.reply_text("Игроков пока нет.")
        return

    text = "👥 Игроки:\n\n"

    for user_id, data in players.items():
        status = "жив" if user_id in alive else "выбыл"
        text += f"• {data['name']} — {status}\n"

    await update.message.reply_text(text)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, roles, alive, votes, game_started

    players = {}
    roles = {}
    alive = set()
    votes = {}
    game_started = False

    await update.message.reply_text("❌ Игра остановлена.")


async def all_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, target = query.data.split(":")
    target_id = int(target)
    user_id = query.from_user.id

    if action == "vote":
        if user_id not in alive:
            await query.edit_message_text("❌ Ты выбыл.")
            return

        if target_id not in alive:
            await query.edit_message_text("❌ Этот игрок уже выбыл.")
            return

        votes[user_id] = target_id

        await query.edit_message_text(
            f"🗳 Ты проголосовал против {players[target_id]['name']}"
        )

        await context.bot.send_message(
            chat_id=group_chat_id,
            text=f"🗳 {players[user_id]['name']} проголосовал."
        )

        return

    await button_handler(update, context)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startgame", startgame))
    app.add_handler(CommandHandler("night", night))
    app.add_handler(CommandHandler("nightresults", nightresults))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("results", results))
    app.add_handler(CommandHandler("players", players_list))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(CallbackQueryHandler(all_buttons))

    print("Бот запущен ✅")
    app.run_polling()


if __name__ == "__main__":
    main()