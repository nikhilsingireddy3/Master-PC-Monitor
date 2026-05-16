from flask import Flask, jsonify, render_template_string
import requests
import csv
from io import StringIO

SHEET_ID = "1EW68VrSfyzaD9UBhWORQe63QOwlz9QLfvQBWx1yWjzI"

app = Flask(__name__)


def send_telegram_message(message):

    bot_token = "8926186497:AAFxCR4OjSpIkRLI1EXtAPiS8yPkVZblEvQ"

    chat_id = "1188618378"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(url, data=payload)

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

    # Correct Hyundai vehicle mappings
    vehicle_mapping = {
        "HYNDN635EE0069980": 39080,
        "HYNDN635CE0069981": 39081,
        "HYNDN635VE0071027": 41970,
        "HYNDN635CE0071026": 41972,
        "HYNDN635EE0071048": 42004,
        "HYNDN635CE0071049": 42006,
        "HYNDE6M4CE0060226": 43261,
        "HYNDE6M4VE0060227": 43258,
        "HYNDE6M4AE0060226": 43261,
        "HYNDE6M4VE0060275": 43391
    }

    sheet_data = get_sheet_data()

    results = []

    for row in sheet_data:

        machine_id = row["Machine ID"]
        pc_no = row["PC No"]
        last_service = row["Last Service Done At"]

        if machine_id not in vehicle_mapping:
            continue

        vehicle_id = vehicle_mapping[machine_id]

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

            response = requests.post(
                url,
                data=params,
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:

                results.append({
                    "PC No": pc_no,
                    "Machine ID": machine_id,
                    "Status": f"HTTP Error {response.status_code}"
                })

                continue

            if not response.text.startswith("{"):

                results.append({
                    "PC No": pc_no,
                    "Machine ID": machine_id,
                    "Status": "Invalid response"
                })

                continue

            json_data = response.json()

            data = json_data.get("data", [])

            if not data:

                results.append({
                    "PC No": pc_no,
                    "Machine ID": machine_id,
                    "Status": "No data"
                })

                continue

            current_hours = None

            for item in reversed(data):

                hm = item.get("HourMeter")

                if hm:

                    h, m = hm.split(":")

                    current_hours = round(
                        float(h) + float(m) / 60,
                        2
                    )

                    break

            if current_hours is None:

                results.append({
                    "PC No": pc_no,
                    "Machine ID": machine_id,
                    "Status": "No valid hour meter"
                })

                continue

            # Service calculations
            last_service = float(last_service) if last_service else 0

            next_service_due = last_service + 500

            remaining_hours = round(
                next_service_due - current_hours,
                2
            )

            # Status logic
            if remaining_hours <= 0:
                status = "OVERDUE"

            elif remaining_hours <= 50:
                status = "DUE SOON"

            else:
                status = "OK"

            results.append({
                "PC No": pc_no,
                "Machine ID": machine_id,
                "Current Hours": current_hours,
                "Last Service Done At": last_service,
                "Next Service Due": next_service_due,
                "Remaining Hours": remaining_hours,
                "Status": status
            })

        except requests.exceptions.Timeout:

            results.append({
                "PC No": pc_no,
                "Machine ID": machine_id,
                "Status": "Timeout"
            })

        except Exception as e:

            results.append({
                "PC No": pc_no,
                "Machine ID": machine_id,
                "Status": str(e)
            })

    # Sort rows by priority
    status_order = {
        "OVERDUE": 0,
        "DUE SOON": 1,
        "OK": 2
    }

    results.sort(
        key=lambda x: status_order.get(x["Status"], 99)
    )

    return results


@app.route("/")
def home():

    data = scrape_hitrack()

    html = """
    <html>

    <head>

        <title>HD Fleet Monitor</title>

        <style>

            body {
                font-family: Arial;
                padding: 20px;
                background-color: #f4f4f4;
            }

            h2 {
                margin-bottom: 20px;
            }

            table {
                border-collapse: collapse;
                width: 100%;
                background: white;
            }

            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: center;
            }

            th {
                background-color: #333;
                color: white;
            }

            .OK {
                background-color: #d4edda;
            }

            .DUE {
                background-color: #fff3cd;
            }

            .OVERDUE {
                background-color: #f8d7da;
            }

        </style>

    </head>

    <body>

        <h2>HD Fleet Monitor</h2>

        <table>

            <tr>
                <th>PC No</th>
                <th>Machine ID</th>
                <th>Current Hours</th>
                <th>Last Service</th>
                <th>Next Due</th>
                <th>Remaining</th>
                <th>Status</th>
            </tr>

            {% for row in data %}

            <tr class="
                {% if row['Status'] == 'OVERDUE' %}
                    OVERDUE
                {% elif row['Status'] == 'DUE SOON' %}
                    DUE
                {% else %}
                    OK
                {% endif %}
            ">

                <td>{{ row['PC No'] }}</td>
                <td>{{ row['Machine ID'] }}</td>
                <td>{{ row['Current Hours'] }}</td>
                <td>{{ row['Last Service Done At'] }}</td>
                <td>{{ row['Next Service Due'] }}</td>
                <td>{{ row['Remaining Hours'] }}</td>
                <td>{{ row['Status'] }}</td>

            </tr>

            {% endfor %}

        </table>

    </body>

    </html>
    """

    return render_template_string(html, data=data)


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
