"""
Seed Flask app for the AgentDEV-MAMA demo.

Serves a small sample employee table via a JSON API, and the frontend
(index.html) renders it.
"""
from flask import Flask, jsonify, send_from_directory, make_response, request
import csv
import io

app = Flask(__name__, static_folder="../frontend", static_url_path="")

EMPLOYEES = [
    {"id": 1, "name": "Asha Rao", "department": "Engineering", "salary": 95000},
    {"id": 2, "name": "Ben Okafor", "department": "Sales", "salary": 72000},
    {"id": 3, "name": "Chen Wei", "department": "Engineering", "salary": 101000},
    {"id": 4, "name": "Diya Patel", "department": "Marketing", "salary": 68000},
    {"id": 5, "name": "Ethan Brooks", "department": "Sales", "salary": 75000},
]


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/employees")
def get_employees():
    search_text = request.args.get('search', '').lower()
    filtered_employees = [emp for emp in EMPLOYEES if search_text in emp['name'].lower()]
    return jsonify(filtered_employees)


@app.route("/export")
def export_csv():
    response = make_response()
    output = io.StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow(["ID", "Name", "Department", "Salary"])
    for emp in EMPLOYEES:
        csv_writer.writerow([emp["id"], emp["name"], emp["department"], emp["salary"]])
    response.headers["Content-Disposition"] = "attachment; filename=employees.csv"
    response.headers["Content-type"] = "text/csv"
    output.seek(0)
    response.data = output.getvalue()
    return response


if __name__ == "__main__":
    app.run(debug=True)