from flask import Flask, render_template, request, redirect, url_for, flash
from threading import Thread, Event
from telegram import Bot
import time
import os

# Explicitly define template folder to avoid TemplateNotFound
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Replace this with your Telegram bot token
TELEGRAM_BOT_TOKEN = "8404307247:AAE3zP7rhltmTmNiG_yCNELAIGxVYIWRXRk"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

running_threads = {}

def send_telegram_messages(chat_id, messages, interval, stop_event):
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set():
                break
            try:
                bot.send_message(chat_id=chat_id, text=msg)
            except Exception as e:
                print(f"Error sending to {chat_id}: {e}")
            time.sleep(interval)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        chat_id = request.form.get("chat_id")
        interval = float(request.form.get("interval", 5))
        file = request.files.get("file")

        if not file or not chat_id:
            flash("All fields are required!")
            return redirect(request.url)

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]

        stop_event = Event()
        thread = Thread(target=send_telegram_messages, args=(chat_id, messages, interval, stop_event))
        thread.start()

        running_threads[chat_id] = {"thread": thread, "stop_event": stop_event}

        flash(f"Started sending messages to {chat_id} every {interval} seconds.")
        return redirect(url_for("index"))

    return render_template("index.html", running_threads=running_threads)

@app.route("/stop/<chat_id>")
def stop(chat_id):
    data = running_threads.get(chat_id)
    if data:
        data["stop_event"].set()
        data["thread"].join()
        running_threads.pop(chat_id)
        flash(f"Stopped sending messages to {chat_id}.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)        if not file or not chat_id:
            flash("All fields are required!")
            return redirect(request.url)

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]

        stop_event = Event()
        thread = Thread(target=send_telegram_messages, args=(chat_id, messages, interval, stop_event))
        thread.start()

        running_threads[chat_id] = {"thread": thread, "stop_event": stop_event}

        flash(f"Started sending messages to {chat_id} every {interval} seconds.")
        return redirect(url_for("index"))

    return render_template("index.html", running_threads=running_threads)

@app.route("/stop/<chat_id>")
def stop(chat_id):
    data = running_threads.get(chat_id)
    if data:
        data["stop_event"].set()
        data["thread"].join()
        running_threads.pop(chat_id)
        flash(f"Stopped sending messages to {chat_id}.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
