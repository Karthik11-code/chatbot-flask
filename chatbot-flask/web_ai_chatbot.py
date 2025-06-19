from flask import Flask, render_template, request
import requests, sqlite3
from fuzzywuzzy import process

API_KEY = "your_serpapi_key_here"

# DB setup
conn = sqlite3.connect("ai_memory_web.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS memory (
    question TEXT PRIMARY KEY,
    answer TEXT
)
''')
conn.commit()

def check_memory(question):
    cursor.execute("SELECT question FROM memory")
    questions = [row[0] for row in cursor.fetchall()]
    match, score = process.extractOne(question, questions)
    if score >= 80:
        cursor.execute("SELECT answer FROM memory WHERE question = ?", (match,))
        return cursor.fetchone()[0]
    return None

def learn(question, answer):
    try:
        cursor.execute("INSERT INTO memory (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
    except:
        pass

def search_google(query):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": API_KEY,
        "engine": "google",
        "num": 1
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        snippet = data['organic_results'][0]['snippet']
        link = data['organic_results'][0]['link']
        return f"{snippet} <br><a href='{link}' target='_blank'>More info</a>"
    except:
        return "No answer found. Try rephrasing."

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    response = ""
    if request.method == "POST":
        question = request.form["question"]
        saved = check_memory(question)
        if saved:
            response = saved
        else:
            response = search_google(question)
            learn(question, response)
    return render_template("index.html", response=response)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

