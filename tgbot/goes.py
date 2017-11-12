import os

from telegram.ext import Updater, CommandHandler
import logging
from telegram.ext import MessageHandler, Filters

from tgbot.googlesearch import google_search
from utils.import_models import get_models_from_yurasic_django

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

yurasic_models = get_models_from_yurasic_django()


def start(bot, update):
    update.message.reply_text('Hello World!')


def hello(bot, update):
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))
    # update.message


def echo(bot, update):
    # global d
    msg = update.message.text
    ans = google_search(msg)

    # wonder = yurasic_models.Wonder(comment=update.message.text)
    # wonder.save()
    # # d += [update.message.text]
    bot.send_message(chat_id=update.message.chat_id, text="I find: " + ans)


# from songsapp import models

def write_list(bot, update):
    ans = ["Comments: "]
    for w in yurasic_models.Wonder.objects.all():
        ans += ["  - " + w.comment]

    ans = os.linesep.join(ans)
    update.message.reply_text(ans)


#################################################

token_str = 'TELEGRAM_BOT_TOKEN'
assert token_str in os.environ.keys()

TOKEN = os.environ.get(token_str)
PORT = int(os.environ.get('PORT', '5000'))

#################################################


updater = Updater(TOKEN)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('hello', hello))
dispatcher.add_handler(CommandHandler('list', write_list))

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
