from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Person(Base):
    __tablename__ = 'quote'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    by = Column(String(50), nullable=True)


updater = Updater(token="554137221:AAGCFwAj3Tk0Oogc80tLFcJmdXOrT05kDAA")
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hoi! Quote bot klaar voor het opnemen van quotes. Begin met"
                                                          "/quote <quote>")

def add_quote(bot, update, args):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

def list_quotes(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

def get_quote(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

def main():
    start_handler = CommandHandler('start', start)
    add_quote_handler = CommandHandler('quote', add_quote)
    echo_handler = MessageHandler(Filters.text, echo)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()





