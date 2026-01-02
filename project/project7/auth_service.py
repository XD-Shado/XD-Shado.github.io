from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if data["password"] == "admin":
        return jsonify({"token": "secure-token"})
    return jsonify({"error": "Unauthorized"}), 401

app.run(port=5001)
