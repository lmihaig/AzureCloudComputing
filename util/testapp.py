from flask import Flask


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def upload():
    return "merge frate"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969)
