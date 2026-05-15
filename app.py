from flask import Flask, jsonify
import requests

app = Flask(__name__)

def scrape_hitrack():
    url = "https://hyundai-ce.live/MachinePerformanceReport/MachinePerformanceReportGridView"

    headers = {
        "Cookie": "c1=CnFrwVPQYlTyNH9CMCopuRURz1ZIKC3E1MPTTQQUCVMV4WzasMge7Au/gOSBVK4c; JSESSIONID=08927079469605A37ECA0A67DA3AB556; AWSELB=A1374585027AECE6E1999905DCA119937B811FE2EEC22DE61210FFA4B37CB8D8B77C27C36B3E4EF67688B7B67A37E592CB9C63DF620D0F3F9DFC96FAFB9EF906057FF5D3868F74A5865066DE92B0AD63D58C712AB1",
        "User-Agent": "Mozilla/5.0"
    }

    # 👉 Add all your machines here
    machines = {
        "HYNDN635EE0069980": 43261,
        # "Machine2": 12345,
        # "Machine3": 67890,
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
            response = requests.get(url, params=params, headers=headers, timeout=20)

            # Safe JSON handling
            try:
                json_data = response.json() if response.text.startswith("{") else {}
            except:
                results[machine_id] = "Invalid response (cookie expired?)"
                continue

            data = json_data.get("data", [])

            if not data:
                results[machine_id] = "No data"
                continue

            # Get latest hour meter
            for row in reversed(data):
                hm = row.get("HourMeter")
                if hm:
                    h, m = hm.split(":")
                    results[machine_id] = round(float(h) + float(m)/60, 2)
                    break

        except Exception as e:
            results[machine_id] = str(e)

    return results


@app.route("/")
def home():
    return jsonify(scrape_hitrack())


# Required for Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
