from flask import Flask, render_template, request, redirect, url_for, flash
from threading import Thread, Event
import os
import requests
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

running_threads = {}

def post_to_facebook(page_token, posts, interval, stop_event):
    url = f"https://graph.facebook.com/v17.0/me/photos?access_token={page_token}"
    idx = 0
    while not stop_event.is_set():
        if idx >= len(posts):
            idx = 0  # Loop back to start
        post = posts[idx]
        image_path = post['image']
        message = post['text']

        try:
            with open(image_path, 'rb') as img_file:
                files = {'source': img_file}
                data = {'caption': message}
                res = requests.post(url, files=files, data=data)
                print(res.json())
        except Exception as e:
            print(f"Error posting: {e}")

        idx += 1
        time.sleep(interval)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        page_token = request.form.get("page_token")
        interval = float(request.form.get("interval", 60))
        images = request.files.getlist("images")
        texts = request.files.getlist("texts")

        if not page_token or not images or not texts:
            flash("All fields are required!")
            return redirect(request.url)

        # Save files
        saved_images = []
        for img in images:
            img_path = os.path.join(UPLOAD_FOLDER, img.filename)
            img.save(img_path)
            saved_images.append(img_path)

        saved_texts = []
        for txt in texts:
            txt_path = os.path.join(UPLOAD_FOLDER, txt.filename)
            txt.save(txt_path)
            with open(txt_path, "r", encoding="utf-8") as f:
                saved_texts.append(f.read().strip())

        # Combine images + texts (1 text → 1 image)
        posts = []
        for i in range(min(len(saved_images), len(saved_texts))):
            posts.append({'image': saved_images[i], 'text': saved_texts[i]})

        stop_event = Event()
        thread = Thread(target=post_to_facebook, args=(page_token, posts, interval, stop_event))
        thread.start()

        running_threads[page_token] = {"thread": thread, "stop_event": stop_event}

        flash("Started automatic posting!")
        return redirect(url_for("index"))

    return render_template("index.html", running_threads=running_threads)

@app.route("/stop/<page_token>")
def stop(page_token):
    data = running_threads.get(page_token)
    if data:
        data["stop_event"].set()
        data["thread"].join()
        running_threads.pop(page_token)
        flash("Stopped posting!")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
