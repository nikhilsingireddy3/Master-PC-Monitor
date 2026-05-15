from flask import Flask, jsonify
import requests

app = Flask(__name__)

def scrape_hitrack():
    url = "https://hyundai-ce.live/MachinePerformanceReport/MachinePerformanceReportGridView"

    headers = {
        "Cookie": "c1=YOUR_COOKIE; JSESSIONID=YOUR_SESSION; AWSELB=YOUR_AWS",
        "User-Agent": "Mozilla/5.0"
    }

    machines = {
        "HYNDN635EE0069980": 43261,
    }

    results = {}

    for machine_id, vehicle_id in machines.items():
        params = {
            "orgId": "126513",
            "vehicleId": vehicle_id,
            "startDate": "2026-05-01 00:00:00",
            "endDate": "2026-05-31 23:59:59",
            "regionId": "0",
            "dealerId": "0",
            "resellerId": "103334",
            "subReselleId": "126512"
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            data = response.json().get("data", [])

            if data:
                hm = data[-1]["HourMeter"]
                h, m = hm.split(":")
                results[machine_id] = round(float(h) + float(m)/60, 2)

        except Exception as e:
            results[machine_id] = str(e)

    return results


@app.route("/")
def home():
    return jsonify(scrape_hitrack())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
