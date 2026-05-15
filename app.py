from flask import Flask, jsonify
import requests

app = Flask(__name__)   # ⭐ THIS IS CRITICAL

def scrape_hitrack():
    return {"status": "working"}   # temporary test


@app.route("/")
def home():
    return jsonify(scrape_hitrack())
