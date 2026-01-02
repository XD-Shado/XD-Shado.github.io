from flask import Flask, request

app = Flask(__name__)

@app.route("/log", methods=["POST"])
def log():
    print("LOG ENTRY:", request.json)
    return "Logged"

app.run(port=5003)
