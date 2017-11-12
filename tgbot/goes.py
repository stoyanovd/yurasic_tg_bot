import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler
import logging
from telegram.ext import MessageHandler, Filters

from default_tg_bot.tg_conf import init_conf
from tgbot.googlesearch import google_search

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(bot, update):
    update.message.reply_text('Hello World!')


def hello(bot, update):
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))
    # update.message


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


def echo(bot, update):
    # global d
    msg = update.message.text
    x = 1
    ans = google_search(msg)


    # html = bs4.BeautifulSoup(r.text, "html.parser")
    # bm.name = html.title.text

    # button_list = [InlineKeyboardButton(bm.name, callback_data='y_' + str(chat.chat_id))]
    # reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))

    # update.message.reply_text("Write name for bookmark, or use hint:", reply_markup=reply_markup)

    # wonder = yurasic_models.Wonder(comment=update.message.text)
    # wonder.save()
    # # d += [update.message.text]
    bot.send_message(chat_id=update.message.chat_id, text="I find: " + ans)


# from songsapp import models

# def write_list(bot, update):
#     ans = ["Comments: "]
#     for w in yurasic_models.Wonder.objects.all():
#         ans += ["  - " + w.comment]
#
#     ans = os.linesep.join(ans)
#     update.message.reply_text(ans)


#################################################
conf = init_conf()


token_str = 'TELEGRAM_BOT_TOKEN'
assert token_str in os.environ.keys()

TOKEN = os.environ.get(token_str)
PORT = int(os.environ.get('PORT', '5000'))

#################################################


updater = Updater(TOKEN)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('hello', hello))
# dispatcher.add_handler(CommandHandler('list', write_list))

dispatcher.add_handler(MessageHandler(Filters.text, echo))

print("finish set up bot.")

updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=str("") + TOKEN)
updater.bot.set_webhook("https://yurasic-tgbot.herokuapp.com/" + TOKEN)

# time to try webhooks
# updater.start_polling()

print("before idle")
updater.idle()
print("after idle")
