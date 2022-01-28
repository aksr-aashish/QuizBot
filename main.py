# A quiz-bot
# Works with groups of up to 200 people, > than that and group converts to a supergroup with a new chat_id, so additional code is needed (chat_ID changes).
# Just /reset it if that would be the case

import constants as keys

import re
import logging

from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Updater, 
    CommandHandler, 
    MessageHandler,
    CallbackQueryHandler, 
    Filters,
    ConversationHandler,
)

# Чтобы точно знать, подключился ли бот к Телеграму или нет
from telegram.utils.request import Request

from db import (
    init_db,
    signup,
    get_chat_ids,
    did_they_answer,
    write_answers,
    write_score,
    round_rating,
    total_score,
    delete_score
)


bot_token = keys.API_TOKEN
admin_id = keys.ADMIN_ID
set_nickname = range(3)
current_phase = 0
question_state = range(2)

# Идентификаторы кнопок
CALLBACK_BUTTON1_LEFT = 'callback_button1_left'
CALLBACK_BUTTON2_CENTRE = 'callback_button2_centre'
CALLBACK_BUTTON3_RIGHT = 'callback_button3_right'

TITLES = {
    CALLBACK_BUTTON1_LEFT: "0",
    CALLBACK_BUTTON2_CENTRE: "1",
    CALLBACK_BUTTON3_RIGHT: "2"
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

# Each list inside "keyboard" is one horizontal row of buttons
# Each item inside the list is one vertical column, as many buttons as there are columns
def get_base_inline_keyboard():
    keyboard = [        
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON1_LEFT], callback_data=CALLBACK_BUTTON1_LEFT),
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON2_CENTRE], callback_data=CALLBACK_BUTTON2_CENTRE),
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON3_RIGHT], callback_data=CALLBACK_BUTTON3_RIGHT)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def keyboard_callback_handler(update, context, chat_data=None, **kwargs):
    # Обработчик ВСЕХ кнопок со ВСЕХ клавиатур
    query = update.callback_query
    data = query.data

    chat_id = update.effective_message.chat_id
    current_text = update.effective_message.text
    nickname = re.findall("(^.+)\s#", current_text, re.DOTALL)[0]

    if data == CALLBACK_BUTTON1_LEFT:
        query.edit_message_text(text=(current_text + "\t#rating: 0 points"))
        rating = 0
        
    elif data == CALLBACK_BUTTON2_CENTRE:
        query.edit_message_text(text=(current_text + "\t#rating: 1 point"))
        rating = 1

    elif data == CALLBACK_BUTTON3_RIGHT:
        query.edit_message_text(text=(current_text + "\t#rating: 2 points"))
        rating = 2

    write_score(nickname=nickname.strip(), rating=rating)

def start_command(update, context):
    '''Allows users to participate in quiz. They enter their names when asked'''
    if current_phase == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! What is your name?")

        return set_nickname
    
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Registration is closed for now, please wait until the end of the current round")

# chat_id is negative if chat is a group, positive if it's a single person "chat"(and equals to user_id in that case)

def user_nickname(update, context):
    '''Ask the user to choose a nickname'''
    user = update.message.from_user
    nickname = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    actual_name = user.first_name
    logger.info("User_id %s registered: in chat_id %s", user_id, chat_id)
    logger.info("User %s has chosen nickname: %s", actual_name, nickname)

    if signup(
        actual_name=actual_name,
        user_id=user_id,
        chat_id=chat_id,
        nickname=nickname,
        answer=0,
        rating=0,
        score=0) == 'OK':

        update.message.reply_text(f"Thanks {nickname}, good luck!")
        return ConversationHandler.END
    
    else:
        update.message.reply_text("A user with the same ID or nickname has already registered")
        return ConversationHandler.END

def invalid_input(update, context):
    update.message.reply_text("Invalid input, please try again")


def admquestion_command(update, context):
    if update.message.from_user.id == admin_id:

        context.bot.send_message(chat_id=update.effective_chat.id, text="What question shall we ask?")

        return question_state
    
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="This command is for administrators only")


def admquestion(update,context):
    global current_phase
    question = update.message.text

    for i in get_chat_ids():
        if i != admin_id:
            context.bot.send_message(chat_id=i, text=question)

            context.bot.pin_chat_message(chat_id=i, message_id=update.message.message_id, disable_notification=None, timeout=None)

    context.bot.send_message(chat_id=update.effective_chat.id, text="I sent the question to all participants, have a nice day")
    current_phase = 1
    return ConversationHandler.END

def answers(update, context):
    if current_phase == 0: pass

    else:
        msg = str(update.message.text)

        if msg.startswith("#answer"):

            user_id=update.message.from_user.id

            if did_they_answer(user_id=user_id) == 0:

                update.message.reply_text("Answer accepted, thanks!")
                get_nick = write_answers(user_id=user_id)
                context.bot.send_message(chat_id=admin_id, text=get_nick+' '+msg, reply_markup=get_base_inline_keyboard())

            else: update.message.reply_text("I'm sorry, but you already gave your answer.")

        else: pass

def admendround_command(update, context):
    '''Announce rating of everyone who scored 1 or 2 points this turn'''

    global current_phase
    results = round_rating()
    postman = get_chat_ids() # Chat_id's of those who *actually* participated!! And only unique ones.
    print(results)

    for i in postman:
        context.bot.send_message(chat_id=i, text=f'Scored 2 points this round: {results[0]}')
        context.bot.send_message(chat_id=i, text=f'But those who scored 1 point for this round: {results[1]}')

    current_phase = 0

def score_command(update, context):

    results = total_score()

    flat_list = []
    for sublist in results:
        for item in sublist:
            flat_list.append(item)    

    context.bot.send_message(chat_id=update.effective_chat.id, text=" ".join(str(x) for x in flat_list))

def admreset_command(update, context):

    if update.message.from_user.id == admin_id:

        delete_score()
        context.bot.send_message(chat_id=update.effective_chat.id, text="All data has been deleted!")
        init_db() #Запускаем новую пустую таблицу
    
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="This command is for administrators only")
    

def main():
    logger.info("Starting the bot")

    req = Request(
        connect_timeout=1.0, # 0.5
        read_timeout=2.0,    # 1.0
    )

    # If a pre-initialized bot is used, it is the user’s responsibility to create it using a Request instance with a large enough connection pool.
    # Add base_url param if you need to use a proxy


    bot = Bot(
        token=bot_token,
        request=req,
    )

    updater = Updater(bot=bot, use_context=True)

    # Проверка, подключились или нет
    info = bot.get_me()
    logger.info(f'Bot info: {info}')

    # Подключаем бд
    init_db()

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            set_nickname: [MessageHandler(Filters.text & ~Filters.command, user_nickname)]
        },
        fallbacks=[MessageHandler(Filters.command, invalid_input)]
    )

    admquestion_handler = ConversationHandler(
        entry_points=[CommandHandler('question', admquestion_command)],
        states={
            question_state: [MessageHandler(Filters.text & ~Filters.command, admquestion)]
        },
        fallbacks=[MessageHandler(Filters.command, invalid_input)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(admquestion_handler)
    dp.add_handler(CommandHandler('round', admendround_command))
    dp.add_handler(CommandHandler('score', score_command))
    dp.add_handler(CommandHandler('reset', admreset_command))
    dp.add_handler(MessageHandler(Filters.text, answers))

    buttons_handler = CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True)
    dp.add_handler(buttons_handler)

    # To start the bot, run:
    updater.start_polling()
    updater.idle()
    logger.info('Bot has been stopped')

if __name__ == "__main__":
    main()
