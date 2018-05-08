from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, Location
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import yaml
from datetime import datetime
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

config = yaml.load(open("config.yml"))

Base = declarative_base()

conversation_data = {}
start_time = datetime.now().strftime("%Y-%m-%d om %H:%M:%S")

class QuoteModel(Base):
    __tablename__ = 'quote'
    id = Column(Integer, primary_key=True)
    quote = Column(Text, nullable=False)
    author = Column(String(50), nullable=True)
    lat = Column(Float, nullable=True)
    long = Column(Float, nullable=True)


class SubscibersModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    subbed = Column(Boolean, nullable=False)


class QuoteConversationMeta:
    quote = None

    def __init__(self):
        self.quote = QuoteModel()


engine = create_engine('sqlite:///quotes.db')
if not os.path.isfile("quotes.db"):
    Base.metadata.create_all(engine)

QUOTE, AUTHOR, LOCATION = range(3)

PROGRAMMA = {
    datetime.strptime("20180508", "%Y%m%d"): "- _10:00 - 15:00_ (ish) Tour door Sofia\n"
                                             "- _15:00 - 18:00_ (optioneel) National Museum met de ReisCo\n"
                                             "- _19:30_ verzamelen voor een gezamelijk avondeten bij een hippe tent in de buurt",
    datetime.strptime("20180509", "%Y%m%d"): "- _10:00_ (optioneel) Museum van Socialistische Kunst met de Reisco\n"
                                             "- _15:30_ Geheime activiteit: Voor iedereen is al betaald dus wees erbij! Verzamelen voor het hostel\n"
                                             "- _20:00_ Vrije avond",
    datetime.strptime("20180510", "%Y%m%d"): "- _10:00_ verzamelen voor het hostel om naar Strypes te gaan.\n"
                                             "Na Strypes gaan we door naar het volgende bedrijf Dreamix. Hier moeten we om 16:00 aanwezig zijn\n"
                                             "- _18:00_ Vrije avond",
    datetime.strptime("20180511", "%Y%m%d"): "- Vrije ochtend\n"
                                             "- _11:45_ verzamelen bij het hostel om samen naar de universiteit te gaan waar we om 13:00 aanwezig moeten zijn.\n"
                                             "- _15:00_ (ish) naar de dierentuin daar in de buurt\n"
                                             "- _21:30_ (ish, optioneel) Pubcrawl, meld je aan bij de ReisCo voor morgen avond",
    datetime.strptime("20180512", "%Y%m%d"): "Vrije dag doe waar je zin in hebt...",
    datetime.strptime("20180513", "%Y%m%d"): "- _10:00_ ingepakt en wel verzamelen bij het hostel we gaan weer naar het vliegtuig."

}

DBSession = sessionmaker(bind=engine)
session = DBSession()

updater = Updater(token=config['telegram']['token'] if 'telegram' in config and 'token' in config['telegram'] else None)
dispatcher = updater.dispatcher

reply_keyboard = [['/cancel', '/submit']]
reply_keyboard_skip = reply_keyboard
quote_keyboard = [['/quotelist', '/programma'],['/quote','/hostel']]


def start(bot, update):
    conversation_data[update.message.chat_id] = QuoteConversationMeta()
    bot.send_message(chat_id=update.message.chat_id, text="Hoi %s! Studiereis bot staat klaar voor het opnemen van "
                                                          "quotes. Begin met /quote om een quote toe te voegen, \n"
                                                          "/programma om het programma in te zien en\n"
                                                          "/hostel om de locatie van ons hostel te krijgen." % update.message.chat.first_name,
                     reply_markup=ReplyKeyboardMarkup(quote_keyboard))




def stop(bot, update):
    update.message.reply_text('Not implemented yet')


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="/quote - Quote toevoegen\n"
                                                          "/quotelist - Quote lijst\n"
                                                          "/programma - Krijg het programma\n"
                                                          "/hostel - Locatie van ons hostel")


def start_quote(bot, update):
    conversation_data[update.message.chat_id] = QuoteConversationMeta()
    bot.send_message(chat_id=update.message.chat_id,
                     text="Welke quote wil je toevoegen?",
                     reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    return QUOTE


def save_quote_text(bot, update):
    conversation_data[update.message.chat_id].quote.quote = update.message.text
    bot.send_message(chat_id=update.message.chat_id,
                     text="Dank je wel. Wie heeft het gezegd?",
                     reply_markup=ReplyKeyboardMarkup(reply_keyboard_skip))
    return AUTHOR


def save_author(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Waar werd het gezegd? Deel a.u.b. je huidige locatie (druk op het 📎 icoon).",
                     reply_markup=ReplyKeyboardMarkup(reply_keyboard_skip))
    conversation_data[update.message.chat_id].quote.author = update.message.text
    return LOCATION


def skip_author(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Ok, ik sla de persoon over. Waar is de opmerking gemaakt?")
    return LOCATION


def save_location(bot, update):
    user_location = update.message.location
    conversation_data[update.message.chat_id].quote.lat = user_location.latitude
    conversation_data[update.message.chat_id].quote.long = user_location.longitude

    bot.send_message(chat_id=update.message.chat_id,
                     text="Ok, locatie bekend.")
    submit_quote(bot, update)
    return ConversationHandler.END


def skip_location(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Ok, ik sla de locatie over.")
    submit_quote(bot, update)
    return ConversationHandler.END


def submit_quote(bot, update):
    if conversation_data[update.message.chat_id].quote.quote:
        save_quote(update.message.chat_id)
        bot.send_message(chat_id=update.message.chat_id,
                         text="De quote is bewaard! Dank je wel!\nZeg /quote om nog een quote toe te voegen.",
                         reply_markup=ReplyKeyboardMarkup(quote_keyboard))
        del conversation_data[update.message.chat_id]
        return ConversationHandler.END
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Volgens mij heb je niks gestuurd. Sad face :(.",
                         reply_markup=ReplyKeyboardMarkup(quote_keyboard))
        return ConversationHandler.END


def save_quote(chat_id):
    quote_model = conversation_data[chat_id].quote
    session.add(quote_model)
    session.commit()
    session.flush()
    return quote_model


def cancel_quote(bot, update):
    if update.message.chat_id in conversation_data:
        del conversation_data[update.message.chat_id]
    update.message.reply_text('Ik heb vergeten wat je gezegd hebt.\nZeg /quote om nog een quote toe te voegen.',
                              reply_markup=ReplyKeyboardMarkup(quote_keyboard))
    return ConversationHandler.END


def get_quotes(bot, update):
    quotes = session.query(QuoteModel).order_by('id desc').limit(20).all()
    message_string = "Dit zijn de nieuwste 20 quotes:\n\n"
    for quote in quotes:
        message_string += "%s - %s\n" % (quote.quote, quote.author)
    update.message.reply_text(message_string,
                              reply_markup=ReplyKeyboardMarkup(quote_keyboard))


def get_program(bot, update):
    now = datetime.now()
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    logger.info("Nu is het %s" % now)
    for key, value in PROGRAMMA.items():
        if key == now:
            update.message.reply_text(value, parse_mode="markdown")

def get_hostel(bot, update):
    update.message.reply_text("Hier is het hostel:\n"
                              "bul. \"Hristo Botev\" 10, 1606 Sofia Center, Sofia, Bulgarije")
    bot.send_location(chat_id=update.message.chat_id, latitude=42.690711, longitude=23.314426)


def get_uptime(bot, update):
    update.message.reply_text("Script is gestart op %s " % start_time)


def main():
    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    help_handler = CommandHandler('help', help)
    program_handler = CommandHandler('programma', get_program)
    quotes_handler = CommandHandler('quotelist', get_quotes)
    hostel_handler = CommandHandler('hostel', get_hostel)
    uptime_handler = CommandHandler('uptime', get_uptime)

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
    dispatcher.add_handler(stop_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(program_handler)
    dispatcher.add_handler(quotes_handler)
    dispatcher.add_handler(hostel_handler)
    dispatcher.add_handler(uptime_handler)

    dispatcher.add_handler(quote_conv_handler)

    updater.start_polling()
    # updater.idle()


if __name__ == "__main__":
    main()
    # get_quotes()
