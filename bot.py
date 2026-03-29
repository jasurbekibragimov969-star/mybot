import telebot
from flask import Flask, request

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Jasurbek bot ishlayapti!"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 Jasurbekning 24/7 aqlli botiga xush kelibsiz!")

@bot.message_handler(func=lambda message: True)
def handle(message):
    bot.reply_to(message, "Sen yozding: " + message.text)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://mybot-4k74.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=10000)
