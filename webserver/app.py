from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        print("WAA")
    return render_template("web.html")


if __name__ == "__main__":
    app.run()
