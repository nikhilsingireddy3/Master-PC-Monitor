from flask import Flask, jsonify
import requests
import csv
from io import StringIO
SHEET_ID = "1EW68VrSfyzaD9UBhWORQe63QOwlz9QLfvQBWx1yWjzI"

app = Flask(__name__)
def get_sheet_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

    response = requests.get(url)

    csv_data = response.text

    reader = csv.DictReader(StringIO(csv_data))

    return list(reader)

def scrape_hitrack():
    url = "https://hyundai-ce.live/MachinePerformanceReport/MachinePerformanceReportGridView"

    headers = {
    "Cookie": "c1=CnFrwVPQYlTyNH9CMCopuRURz1ZIKC3E1MPTTQQUCVMV4WzasMge7Au/gOSBVK4c; JSESSIONID=08927079469605A37ECA0A67DA3AB556; AWSELB=A1374585027AECE6E1999905DCA119937B811FE2EEC22DE61210FFA4B37CB8D8B77C27C36B3E4EF67688B7B67A37E592CB9C63DF620D0F3F9DFC96FAFB9EF906057FF5D3868F74A5865066DE92B0AD63D58C712AB1",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://hyundai-ce.live/jsp/Templates/MachinePerformanceReport.jsp"

    }

    # 👉 Add all your machines here
     sheet_data = get_sheet_data()

     machines = {}

     vehicle_mapping = {
    "HYNDN635EE0069980": 43261,
    "HYNDN635CE0069981": 43262,
    "HYNDN635VE0071027": 43263,
    "HYNDN635CE0071026": 43264,
    "HYNDN635EE0071048": 43265,
    "HYNDN635CE0071049": 43266,
    "HYNDE6M4CE0060226": 43267,
    "HYNDE6M4VE0060227": 43268,
    "HYNDE6M4AE0060226": 43269,
    "HYNDE6M4VE0060275": 43270
}

for row in sheet_data:
    machine_id = row["Machine ID"]

    if machine_id in vehicle_mapping:
        machines[machine_id] = vehicle_mapping[machine_id]

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
            response = requests.post(url, data=params, headers=headers, timeout=20)

            # ✅ Check HTTP response
            if response.status_code != 200:
                results[machine_id] = f"HTTP Error {response.status_code}"
                continue

            # ✅ Safe JSON parsing
            if not response.text.startswith("{"):
                results[machine_id] = "Invalid response (cookie expired?)"
                continue

            json_data = response.json()
            data = json_data.get("data", [])

            if not data:
                results[machine_id] = "No data"
                continue

            # ✅ Extract latest hour meter
            latest_found = False
            for row in reversed(data):
                hm = row.get("HourMeter")
                if hm:
                    try:
                        h, m = hm.split(":")
                        results[machine_id] = round(float(h) + float(m)/60, 2)
                        latest_found = True
                        break
                    except:
                        continue

            if not latest_found:
                results[machine_id] = "No valid hour meter"

        except requests.exceptions.Timeout:
            results[machine_id] = "Timeout"
        except Exception as e:
            results[machine_id] = str(e)

    return results


@app.route("/")
def home():
    return get_sheet_data()


# Required for Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
