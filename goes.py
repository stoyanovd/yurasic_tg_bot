import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

from default_tg_bot.tg_conf import init_conf

conf = init_conf()

from pony.orm import commit
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import Updater, CommandHandler

from pony import orm
import default_tg_bot.orm_setup
from default_tg_bot.orm_setup import Chat, Bookmark, Tag
from default_tg_bot.orm_setup import WorkStateEnum

import requests
import bs4


#################################################

# TgBot some example command realizations

def start(bot, update):
    update.message.reply_text('Hello World!')


def hello(bot, update):
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))


#################################################


@orm.db_session
def get_chat(update):
    chat_id = update.message.chat.id
    print("I get chat_id: " + str(chat_id))

    chat = Chat.get(chat_id=chat_id)
    if not chat:
        chat = Chat(chat_id=chat_id)
        update.message.reply_text("Hi in new chat.")
    commit()
    return chat


@orm.db_session
def get_bm(chat, msg, update):
    if Bookmark.get(owner=chat, url=msg):
        print("I already have this link. It will be rewritten.")
        bm = Bookmark.get(owner=chat, url=msg)
        update.message.reply_text("I already have this link. It will be rewritten.")
    else:
        print("I create new bm.")
        bm = Bookmark(url=msg, owner=chat)
        update.message.reply_text("I create new bm.")
    commit()
    return bm


@orm.db_session
def com_handler_add_bm_get_chat(bot, update):
    chat = get_chat(update)

    chat.state = int(WorkStateEnum.Add_Url)
    update.message.reply_text("Please write url:")


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


@orm.db_session
def mid_handler_add_bm_get_url(msg, chat, update):
    bm = get_bm(chat, msg, update)

    r = requests.get(bm.url)
    html = bs4.BeautifulSoup(r.text, "html.parser")
    bm.name = html.title.text

    button_list = [InlineKeyboardButton(bm.name, callback_data='y_' + str(chat.chat_id))]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))

    update.message.reply_text("Write name for bookmark, or use hint:", reply_markup=reply_markup)
    chat.state = int(WorkStateEnum.Add_Name)
    chat.current_bm = bm.url


@orm.db_session
def mid_handler_add_bm_get_name(msg, chat, update, bot=None):
    bm = Bookmark.get(owner=chat, url=chat.current_bm)
    assert bm
    if msg and msg != 'y':
        bm.name = msg

    bot.send_message(chat.chat_id, "Please write a lot of tags separated by spaces:")
    chat.state = int(WorkStateEnum.Add_Tags)


@orm.db_session
def get_tag(name):
    tag = Tag.get(name=name)
    if not tag:
        tag = Tag(name=name)
    commit()
    return tag


@orm.db_session
def mid_handler_add_bm_add_tags(msg, chat, update):
    bm = Bookmark.get(url=chat.current_bm)
    tags_name = msg.split(' ')
    tags = [get_tag(s) for s in tags_name]
    bm.tags = tags

    update.message.reply_text("We add these tags:")
    update.message.reply_text(str([tag.name for tag in bm.tags]))

    update.message.reply_text("Finish adding bookmark.")
    chat.state = int(WorkStateEnum.Nothing)


command_resolver = {
    int(WorkStateEnum.Nothing): lambda *args: 1,
    int(WorkStateEnum.Add_Url): mid_handler_add_bm_get_url,
    int(WorkStateEnum.Add_Name): mid_handler_add_bm_get_name,
    int(WorkStateEnum.Add_Tags): mid_handler_add_bm_add_tags,
}


@orm.db_session
def all_common_messages_handler(bot, update):
    chat = get_chat(update)

    msg = update.message.text

    callback = command_resolver[chat.state]
    if callback:
        callback(msg, chat, update)

        # bot.send_message(chat_id=update.message.chat_id, text=ans)


@orm.db_session
def com_handler_list(bot, update):
    chat = get_chat(update)

    ans = ""
    for bm in chat.bm:
        ans += "url=" + bm.url + os.linesep + "(name=" + bm.name + ")" \
               + os.linesep \
               + " ".join([tag.name for tag in bm.tags]) \
               + os.linesep

    update.message.reply_text("----------")
    if ans:
        update.message.reply_text(ans)
        update.message.reply_text("----------")


@orm.db_session
def com_handler_stop(bot, update):
    chat = get_chat(update)

    chat.state = int(WorkStateEnum.Nothing)
    update.message.reply_text("Ok. All is finished.")


@orm.db_session
def callback_handler_func(bot, update):
    # chat = get_chat(update)

    print("we in callbackHandler")

    query = update.callback_query.data
    if not query.startswith('y_'):
        print("we in callbackHandler. str is " + query)
        return
    print("we in callbackHandler find 'y'")
    chat_id = int(query[2:])

    chat = Chat.get(chat_id=chat_id)
    if not chat:
        chat = Chat(chat_id=chat_id)
        bot.send_message(chat_id, "Hi in new chat.")
    commit()

    mid_handler_add_bm_get_name('y', chat, update, bot)


@orm.db_session
def com_handler_clean_all(bot, update):
    chat = get_chat(update)

    chat.state = int(WorkStateEnum.Nothing)
    # bms = chat.bm
    # for bm in bms:
    chat.bm.select(lambda x: True).delete(bulk=True)
    # orm.delete(bm for bm in chat.bm)
    chat.current_bm = None
    update.message.reply_text("Ok. All is finished.")


#################################################

# TgBot pipeline

def set_up_bot(conf):
    updater = Updater(conf.TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))

    dispatcher.add_handler(CommandHandler('hello', hello))

    dispatcher.add_handler(CommandHandler('add', com_handler_add_bm_get_chat))
    dispatcher.add_handler(CallbackQueryHandler(callback_handler_func))

    dispatcher.add_handler(CommandHandler('clean_all', com_handler_clean_all))
    dispatcher.add_handler(CommandHandler('stop', com_handler_stop))
    dispatcher.add_handler(CommandHandler('list', com_handler_list))

    dispatcher.add_handler(MessageHandler(Filters.text, all_common_messages_handler))

    print("finish set up bot.")
    return updater


#################################################

"""
hello - Test it works
add - Add new bookmark
clean_all - Clean all bookmarks
stop - Stop asking for details and finish
list - List all bookmarks
"""


# TODO nice Finite State Machine (FSM) library:
# https://github.com/pytransitions/transitions

#################################################

def start_webhooks(updater, conf):
    updater.start_webhook(listen="0.0.0.0",
                          port=conf.PORT,
                          url_path=str("") + conf.TOKEN)
    updater.bot.set_webhook(conf.WEBHOOK_URL_PREFIX + conf.TOKEN)


def start_polling(updater):
    updater.start_polling()


def main():
    updater = set_up_bot(conf)

    # for heroku
    start_webhooks(updater, conf)
    # OR
    # for run from your computer
    # start_polling(updater)

    print("before idle")
    updater.idle()
    print("after idle")


if __name__ == '__main__':
    main()
