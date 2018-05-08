from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup
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
    datetime.strptime("20180507", "%Y%m%d"): "Op maandag 7 mei vertrekken wij vanaf 11:30 Leiden Centraal richting "
                                             "Eindhoven. We vliegen om 16:20 en komen aan om 20:00 in Sofia. Houd "
                                             "rekening met het tijdsverschil! In Sofia is het namelijk een uurtje "
                                             "later. Je hoeft niet perse met ons mee te reizen naar Eindhoven. Maar "
                                             "als je er niet bent wacht het vliegtuig niet. Zorg dus dat je op tijd "
                                             "bent!\nAls we zijn aangekomen vertrekken wij richting het hostel met de "
                                             "metro. Na de metro is het nog ongeveer 15 minuten lopen en dan zijn we "
                                             "er. Zodra iedereen een plekje heeft en zijn spullen heeft weggelegd "
                                             "hebben jullie vrij voor de rest van de avond om de omgeving te kunnen "
                                             "verkennen.",
    datetime.strptime("20180508", "%Y%m%d"): "Rise and shine! Vandaag hebben we een tour door de stad heen. We willen "
                                             "rond 10:30 verzamelen voor het hostel om vervolgens om 10:45 te "
                                             "vertrekken naar de tour die rond 11:00 begint. Vergeet je goede "
                                             "wandelschoenen niet aan te trekken. De tour zal een kleine anderhalf "
                                             "duren. \nIn de middag kan je aansluiten bij de ReisCo wanneer we naar "
                                             "het national museum gaan :). Een voorproefje kun je op de site vinden. "
                                             "https://historymuseum.org/\nIn de avond verzamelen we om 19:30 en gaan "
                                             "we lekker met elkaar gezellig wat smikkelen*. Dit is elk jaar weer een "
                                             "groot feest waar we graag iedereen bij zouden zien! Mocht het zo zijn "
                                             "dat je, om wat voor reden dan ook, hier niet bij aanwezig bent, "
                                             "dan willen wij dit graag voor aanvang van de studiereis weten. Dit om "
                                             "te voorkomen dat we te maken krijgen met boze restaurantmedewerkers.\n* "
                                             "De kosten voor het eten zijn voor eigen rekening, tenzij anders vermeld.",
    datetime.strptime("20180509", "%Y%m%d"): "Vandaag hebben we in de ochtend en het begin van de middag vrij, "
                                             "chill! \nIn de ochtend kan je naar een leuk museum gaan met de "
                                             "reiscommissie, namelijk het socialistische kunst museum.\nIn de middag "
                                             "kan je eventueel mee naar een groot winkelcentrum, deze zijn door de "
                                             "hele stad te vinden. \nMocht je dat echt niet willen, zijn er nog "
                                             "genoeg alternatieven, open je internet en kijk voor wat leuks in de "
                                             "buurt!\nOm 15:30 verzamelen we weer bij het hostel. Vervolgens is het "
                                             "tijd voor een leuke activiteit, die tot op locatie geheim blijft!",
    datetime.strptime("20180510", "%Y%m%d"): "Vandaag hebben we een studiegerichte activiteit voor jullie! Om 11:00 "
                                             "worden wij verwacht bij Strypes. De planning is om 10:15 te verzamelen "
                                             "voor het hostel. Als we compleet zijn vertrekken we richting het "
                                             "bedrijf.\n‘s Middags is er een tweede bedrijvenbezoek gepland. Omdat "
                                             "deze nog niet helemaal vast staat kunnen wij de hoe en wat nu nog niet "
                                             "vertellen. Dit krijgen jullie in een later stadium van ons te horen. "
                                             "Mocht deze activiteit niet doorgaan hebben jullie vrije tijd maar dan "
                                             "zouden jullie wel aan kunnen sluiten bij de ReisCo die dan een "
                                             "foodtasting tour gaat doen: http://bit.ly/sofiareis_foodtasting\nIn de "
                                             "avond is er een pubcrawl gepland en het gaat gegarandeerd een gezellige "
                                             "avond worden!",
    datetime.strptime("20180511", "%Y%m%d"): "Wij willen vrijdag graag naar de technische universiteit van Sofia, "
                                             "echter staat dit nog niet vast en laat de universiteit op zich "
                                             "wachten.\nMocht dit niet doorgaan dan is deze dag vrij te besteden! Ga "
                                             "wat leuks doen, huur een fiets, of bezoek een van de vele biertuinen. "
                                             "Denk ook terug aan de tour, heb je wat leuks gezien waar je nog heen "
                                             "wilde? Nu is de kans om dat te doen.\nEen aantal leden van de ReisCo "
                                             "gaan in de middag naar de dierentuin. Om 12:30 staan wij voor het "
                                             "hostel en vertrekken we naar de dierentuin.",
    datetime.strptime("20180512", "%Y%m%d"): "Vandaag hebben we bewust vrij gehouden. Nog dingen die je wilde doen? "
                                             "Nog magneetjes nodig voor op de koelkast? Of nog een leuk cadeau voor "
                                             "je bae thuis. Vandaag is het de dag om het te kopen. Ook kun je de dag "
                                             "goed besteden door een bezoek te brengen aan het Rela Monestary! "
                                             "http://bit.ly/sofiareis_rila\nVoor eventuele vragen of andere dingen "
                                             "kun je bij de Nederlandse Ambassade terecht, de ReisCo heeft vandaag "
                                             "vrij!",
    datetime.strptime("20180513", "%Y%m%d"): "D-Day. Het is 2018, het is een warme zomerdag in Sofia, vandaag vliegen "
                                             "we weer terug naar het thuisfront. Om 14:05 vertrekt ons vliegtuig en "
                                             "om 15:45 komen we weer aan in ons geliefde vaderland. Om 11:00 moeten "
                                             "we uitgecheckt zijn bij het hostel. Vanaf daar is aan ons om op ons "
                                             "gemak richting het vliegveld te reizen."

}

DBSession = sessionmaker(bind=engine)
session = DBSession()

updater = Updater(token=config['telegram']['token'] if 'telegram' in config and 'token' in config['telegram'] else None)
dispatcher = updater.dispatcher

reply_keyboard = [['/cancel', '/submit']]
reply_keyboard_skip = reply_keyboard
quote_keyboard = [['/quotelist', '/programma', '/quote']]


def start(bot, update):
    conversation_data[update.message.chat_id] = QuoteConversationMeta()
    bot.send_message(chat_id=update.message.chat_id, text="Hoi %s! Studiereis bot staat klaar voor het opnemen van "
                                                          "quotes. Begin met /quote om een quote toe te voegen" % update.message.chat.first_name)


def stop(bot, update):
    update.message.reply_text('Not implemented yet')


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="/quote - Quote toevoegen\n"
                                                          "/quotelist - Quote lijst\n"
                                                          "/programma - Krijg het programma")


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
            update.message.reply_text(value)


def main():
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    program_handler = CommandHandler('programma', get_program)
    quotes_handler = CommandHandler('quotelist', get_quotes)

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
    dispatcher.add_handler(program_handler)
    dispatcher.add_handler(quotes_handler)

    dispatcher.add_handler(quote_conv_handler)

    updater.start_polling()
    # updater.idle()


if __name__ == "__main__":
    main()
    # get_quotes()
