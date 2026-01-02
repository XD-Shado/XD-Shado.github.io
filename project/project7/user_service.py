from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/user")
def user():
    return jsonify({"name": "Demo User", "role": "Student"})

app.run(port=5002)
