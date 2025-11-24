from flask import Flask, render_template, request, send_file
import csv
import os

app = Flask(__name__)

# 定義星期與節次
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PERIODS = [f"Period {i}" for i in range(1, 13)]  # 1~12 節

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 建立 schedule.csv
        filename = "schedule.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header = ["Day"] + PERIODS
            writer.writerow(header)

            for day in WEEKDAYS:
                row = [day]
                for p in PERIODS:
                    key = f"{day}_{p}".replace(" ", "_")
                    row.append(request.form.get(key, ""))
                writer.writerow(row)

        return send_file(filename, as_attachment=True)

    return render_template("index.html",
                           weekdays=WEEKDAYS,
                           periods=PERIODS)

if __name__ == "__main__":
    app.run(debug=True)
