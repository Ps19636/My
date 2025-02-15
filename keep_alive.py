from flask import Flask, render_template
from threading import Thread

app = Flask(__name__)
@app.route('/')
def index():
    return "Alive"

def run():
    app.run(host='16.16.192.146',port=22)

def keep_alive():
    t = Thread(target=run)
    t.start()    