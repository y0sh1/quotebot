from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

conversation_data = {}

class QuoteModel(Base):
    __tablename__ = 'quote'
    id = Column(Integer, primary_key=True)
    quote = Column(Text, nullable=False)
    author = Column(String(50), nullable=True)
    lat = Column(Float, nullable=True)
    long = Column(Float, nullable=True)

class QuoteConversationMeta:
    quote = None

    def __init__(self):
        self.quote = QuoteModel()

engine = create_engine('sqlite:///quotes.db')
if not os.path.isfile("quotes.db"):
    Base.metadata.create_all(engine)

QUOTE, AUTHOR, LOCATION = range(3)

DBSession = sessionmaker(bind=engine)
session = DBSession()

updater = Updater(token="554137221:AAGCFwAj3Tk0Oogc80tLFcJmdXOrT05kDAA")
dispatcher = updater.dispatcher

reply_keyboard = [['/cancel', '/submit']]
reply_keyboard_skip = [['/cancel', '/skip', '/submit']]
quote_keyboard = [['/quote_list', '/quote']]


def start(bot, update):
    conversation_data[update.message.chat_id] = QuoteConversationMeta()
    bot.send_message(chat_id=update.message.chat_id, text="Hoi! Quote bot klaar voor het opnemen van quotes. Begin met "
                                                          "/quote om een quote toe te voegen")

def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="/quote - Quote toevoegen\n"
                                                          "/quote_list - Quote lijst")

def start_quote(bot, update):
    conversation_data[update.message.chat_id] = QuoteConversationMeta()
    bot.send_message(chat_id=update.message.chat_id, text="Welke quote wil je toevoegen?", reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    return QUOTE


def save_quote_text(bot, update):
    conversation_data[update.message.chat_id].quote.quote = update.message.text
    bot.send_message(chat_id=update.message.chat_id, text="Dank je wel. Wie heeft het gezegd?", reply_markup=ReplyKeyboardMarkup(reply_keyboard_skip))
    return AUTHOR

def save_author(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Waar werd het gezegd? Deel a.u.b. je huidige locatie, of kies /skip.", reply_markup=ReplyKeyboardMarkup(reply_keyboard_skip))
    conversation_data[update.message.chat_id].quote.author = update.message.text
    return LOCATION

def skip_author(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Ok, ik sla de persoon over.")
    return LOCATION

def save_location(bot, update):
    user = update.message.from_user
    user_location = update.message.location
    conversation_data[update.message.chat_id].quote.lat = user_location.latitude
    conversation_data[update.message.chat_id].quote.long = user_location.longitude

    bot.send_message(chat_id=update.message.chat_id, text="Ok, locatie bekend.")
    submit_quote(bot, update)
    return ConversationHandler.END

def skip_location(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Ok, ik sla de locatie over.")
    submit_quote(bot, update)
    return ConversationHandler.END

def submit_quote(bot, update):
    save_quote(update.message.chat_id)

    bot.send_message(chat_id=update.message.chat_id, text="Quote is bewaard! Dank je wel!",
                     reply_markup=ReplyKeyboardMarkup(quote_keyboard))
    return ConversationHandler.END


def save_quote(chat_id):
    quote_model = conversation_data[chat_id].quote
    session.add(quote_model)
    session.commit()
    return quote_model


# def list_quotes(bot, update):
#     bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def cancel_quote(bot, update):
    conversation_data[update.message.chat_id] = None
    update.message.reply_text('Ik zal vergeten wat je gezegd hebt.',
                              reply_markup=ReplyKeyboardMarkup(quote_keyboard))
    return ConversationHandler.END


def main():
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)

    quote_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('quote', start_quote)],

        states={
            QUOTE: [MessageHandler(Filters.text, save_quote_text)],
            AUTHOR: [MessageHandler(Filters.text, save_author),
                    CommandHandler('skip', skip_author)],

            LOCATION: [MessageHandler(Filters.location, save_location),
                       CommandHandler('skip', skip_location)]

        },
        fallbacks=[CommandHandler('submit', submit_quote), CommandHandler('cancel', cancel_quote)]
    )

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)

    dispatcher.add_handler(quote_conv_handler)

    updater.start_polling()
    # updater.idle()


if __name__ == "__main__":
    main()
