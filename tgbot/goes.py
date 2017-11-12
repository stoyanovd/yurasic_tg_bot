import os
import urllib.parse

import yaml
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging
from telegram.ext import MessageHandler, Filters

from default_tg_bot.tg_conf import init_conf
from tgbot.googlesearch import google_search, GSEARCH_displayLink, url_clean_http_www, create_iv_link

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


def get_hostname(url):
    from urllib.parse import urlparse
    parsed_uri = urlparse(url)
    return parsed_uri.hostname
    # domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)


def echo(bot, update):
    msg = update.message.text

    results = google_search(msg)

    # html = bs4.BeautifulSoup(r.text, "html.parser")
    # bm.name = html.title.text

    # urllib.parse.quote_plus(pprint.pformat(result))

    # button_list = [InlineKeyboardButton(bm.name, callback_data='y_' + str(chat.chat_id))]
    print('We start to create buttons...')

    button_list = []
    for r in results:
        line = []
        if 'iv' in r:
            r['chat_id'] = update.message.chat_id
            b = InlineKeyboardButton(text="Instant View",
                                     callback_data='y_' + r['link'])  # + urllib.parse.quote_plus(r['iv']))
            line += [b]

        b = InlineKeyboardButton(text="{:20} | ".format(get_hostname(r[GSEARCH_displayLink])) + r['title'],
                                 url=r['link'])
        line += [b]

        button_list += [line]

    reply_markup = InlineKeyboardMarkup(button_list)
    print('We are trying to send buttons_menu...')
    update.message.reply_text("Results:", reply_markup=reply_markup)

    # bot.send_message(chat_id=update.message.chat_id, text="I find: " + ans)


def callback_handler_func(bot, update):
    # chat = get_chat(update)

    print("we in callbackHandler")

    query = update.callback_query.data
    if not query.startswith('y_'):
        print("we in callbackHandler. str is " + query)
        return
    print("we in callbackHandler find 'y'")
    full_link = query[2:]
    # cleaned_link = url_clean_http_www(full_link)
    # cleaned_link = cleaned_link[:cleaned_link.find('/')]
    iv_link = create_iv_link(full_link, get_hostname(full_link))

    print("we in callbackHandler ready to send message")
    bot.send_message(chat_id=update.callback_query.message.chat.id, text="IV link: " + "\n" + iv_link)

    # chat = Chat.get(chat_id=chat_id)
    # if not chat:
    #     chat = Chat(chat_id=chat_id)
    #     bot.send_message(chat_id, "Hi in new chat.")
    # commit()
    #
    # mid_handler_add_bm_get_name('y', chat, update, bot)


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
dispatcher.add_handler(CallbackQueryHandler(callback_handler_func))

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
