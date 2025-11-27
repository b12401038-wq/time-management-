from flask import Flask, render_template, request, jsonify, send_file
import csv
import os
from html2image import Html2Image

app = Flask(__name__)

DAYS = ["一", "二", "三", "四", "五", "六", "日"]
PERIODS = list(range(1, 13))


@app.route("/")
def index():
    schedule = {}

    if os.path.exists("courses.csv"):
        with open("courses.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                day, period, name = row
                schedule[(day, period)] = name

    return render_template("index.html", days=DAYS, periods=PERIODS, schedule=schedule)


@app.post("/save")
def save():
    data = request.json
    with open("courses.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for item in data:
            writer.writerow([item["day"], item["period"], item["name"]])
    return jsonify({"status": "ok"})


@app.route("/export_png")
def export_png():
    hti = Html2Image()
    hti.output_path = "."
    hti.screenshot(
        url="http://127.0.0.1:5000/",
        save_as="schedule.png",
        size=(1200, 900)
    )
    return send_file("schedule.png", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
