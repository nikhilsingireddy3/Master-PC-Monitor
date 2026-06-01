from flask import Flask, render_template_string, send_from_directory
import requests
import csv
import gspread
from io import StringIO
from datetime import datetime
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

sheet = None

try:
    creds = Credentials.from_service_account_file(
        "/etc/secrets/credentials.json",
        scopes=SCOPES
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_key(
        "1EW68VrSfyzaD9UBhWORQe63QOwlz9QLfvQBWx1yWjzI"
    ).sheet1

    print("Google Sheet Connected")

except Exception as e:

    print("Google Sheet Error:", e)
app = Flask(__name__)





# ====================================
# CONFIG
# ====================================

SHEET_ID = "1EW68VrSfyzaD9UBhWORQe63QOwlz9QLfvQBWx1yWjzI"

BOT_TOKEN = "8926186497:AAFxCR4OjSpIkRLI1EXtAPiS8yPkVZblEvQ"

CHAT_IDS = [
    "1188618378",
    "8615932622"
]

# ====================================
# BACKGROUND IMAGE
# ====================================


@app.route('/background.jpeg')
def background():
    return send_from_directory('.', 'background.jpeg')


# ====================================
# TELEGRAM
# ====================================


def send_telegram_message(message):

    try:

        for chat_id in CHAT_IDS:

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": message
            }

            requests.post(
                url,
                data=payload,
                timeout=10
            )

    except Exception as e:

        print(e)


# ====================================
# GOOGLE SHEET
# ====================================


def get_sheet_data():

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

    response = requests.get(
        url,
        timeout=10
    )

    csv_data = response.text

    reader = csv.DictReader(StringIO(csv_data))

    return list(reader)


# ====================================
# HYUNDAI SCRAPER
# ====================================


def scrape_hitrack():

    url = "https://hyundai-ce.live/MachinePerformanceReport/MachinePerformanceReportGridView"

    headers = {
        "Cookie": "c1=CnFrwVPQYlTyNH9CMCopuRURz1ZIKC3E1MPTTQQUCVMV4WzasMge7Au/gOSBVK4c; JSESSIONID=08927079469605A37ECA0A67DA3AB556; AWSELB=A1374585027AECE6E1999905DCA119937B811FE2EEC22DE61210FFA4B37CB8D8B77C27C36B3E4EF67688B7B67A37E592CB9C63DF620D0F3F9DFC96FAFB9EF906057FF5D3868F74A5865066DE92B0AD63D58C712AB1",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://hyundai-ce.live/jsp/Templates/MachinePerformanceReport.jsp"
    }

    vehicle_mapping = {
        "HYNDN635EE0069980": 39080,
        "HYNDN635CE0069981": 39081,
        "HYNDN635VE0071027": 41970,
        "HYNDN635CE0071026": 41972,
        "HYNDN635EE0071048": 42004,
        "HYNDN635CE0071049": 42006,
        "HYNDE6M4CE0060226": 43261,
        "HYNDE6M4VE0060227": 43258,
        "HYNDE6M4AE0060276": 43392,
        "HYNDE6M4VE0060275": 43391
    }
    
    sheet_data = get_sheet_data()

    results = []

    for row in sheet_data:

        machine_id = row["Machine ID"]
        pc_no = row["PC No"]

        try:
            last_service = float(
                row["Last Service Done At"]
            )
        except:
            last_service = 0

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
                timeout=10
            )

            json_data = response.json()

            data = json_data.get(
                "data",
                []
            )

            current_hours = 0

            for item in reversed(data):

                hm = item.get("HourMeter")

                if hm:

                    h, m = hm.split(":")

                    current_hours = round(
                        float(h) + float(m) / 60,
                        2
                    )

                    break

            next_service_due = (
                last_service + 500
            )

            remaining_hours = round(
                next_service_due - current_hours,
                2
            )

            if remaining_hours <= 0:

                status = "OVERDUE"

            elif remaining_hours <= 50:

                status = "DUE SOON"

            else:

                status = "OK"

            results.append({
                "Row ID": row["Row ID"],
                "PC No": pc_no,

                "Machine ID": machine_id,

                "Current Hours": current_hours,

                "Last Service Done At": last_service,

                "Next Service Due": next_service_due,

                "Remaining Hours": remaining_hours,

                "Status": status
                
            })

        except Exception as e:

            print(e)

    status_order = {
        "OVERDUE": 0,
        "DUE SOON": 1,
        "OK": 2
    }

    results.sort(
        key=lambda x: status_order.get(
            x["Status"],
            99
        )
    )

    return results


# ====================================
# DASHBOARD
# ====================================


@app.route("/")
def home():

    data = scrape_hitrack()

    overdue_count = len([
        x for x in data
        if x["Status"] == "OVERDUE"
    ])

    due_soon_count = len([
        x for x in data
        if x["Status"] == "DUE SOON"
    ])

    ok_count = len([
        x for x in data
        if x["Status"] == "OK"
    ])

    html = """

    <html>

    <head>

        <title>
            MASTERS PC Service Monitor Dashboard
        </title>

        <meta http-equiv="refresh" content="300">

        <style>

            body {

                font-family: Arial;

                padding: 20px;

                background-image: url('/background.jpeg');

                background-size: cover;

                background-position: center;

                background-attachment: fixed;

                color: white;
            }

            body::before {

                content: "";

                position: fixed;

                top: 0;
                left: 0;

                width: 100%;
                height: 100%;

                background: rgba(0,0,0,0.55);

                z-index: -1;
            }

            .summary {

                display: flex;

                gap: 20px;

                margin-bottom: 20px;
            }

            .card {

                padding: 20px;

                border-radius: 12px;

                color: white;

                font-size: 20px;

                font-weight: bold;

                width: 180px;

                text-align: center;

                backdrop-filter: blur(10px);

                background: rgba(255,255,255,0.15);

                border: 1px solid rgba(255,255,255,0.2);

                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            }

            .red {
                background: rgba(220,53,69,0.8);
            }

            .yellow {
                background: rgba(255,193,7,0.8);
                color: black;
            }

            .green {
                background: rgba(40,167,69,0.8);
            }

            table {

                width: 100%;

                border-collapse: collapse;

                background: rgba(255,255,255,0.12);

                backdrop-filter: blur(12px);

                border-radius: 12px;

                overflow: hidden;
            }

            th, td {

                border: 1px solid rgba(255,255,255,0.15);

                padding: 12px;

                text-align: center;

                color: white;
            }

            th {

                background: rgba(0,0,0,0.7);

                color: white;
            }

            .OK {
                background-color: rgba(40,167,69,0.25);
            }

            .DUE {
                background-color: rgba(255,193,7,0.25);
            }

            .OVERDUE {
                background-color: rgba(220,53,69,0.25);
            }

            button {

                padding: 12px 18px;

                background: #007bff;

                color: white;

                border: none;

                border-radius: 8px;

                margin-bottom: 20px;

                cursor: pointer;

                font-size: 15px;

                font-weight: bold;

                box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            }

            h1 {

                text-shadow: 2px 2px 8px black;
            }

        </style>

    </head>

    <body>

        <h1>
            MASTERS PC Service Monitor Dashboard
        </h1>

        <div class="summary">

            <div class="card red">
                OVERDUE<br><br>
                {{ overdue_count }}
            </div>

            <div class="card yellow">
                DUE SOON<br><br>
                {{ due_soon_count }}
            </div>

            <div class="card green">
                OK<br><br>
                {{ ok_count }}
            </div>

        </div>

        <button onclick="window.location.href='/send-alert'">

            Send Telegram Alert

        </button>

        <table>

            <tr>
                <th>PC No</th>
                <th>Machine ID</th>
                <th>Current Hours</th>
                <th>Last Service</th>
                <th>Next Due</th>
                <th>Remaining</th>
                <th>Status</th>
                <th>Action</th>
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
                <td>
                    <a href="/mark-service/{{ row['Row ID'] }}">
                        <button>
                            Mark Service Done
                        </button>
                    </a>
                </td>

            </tr>

            {% endfor %}

        </table>

    </body>

    </html>

    """

    return render_template_string(
        html,
        data=data,
        overdue_count=overdue_count,
        due_soon_count=due_soon_count,
        ok_count=ok_count
    )


# ====================================
# TEST GOOGLE SHEET
# ====================================

@app.route("/test-sheet")
def test_sheet():

    try:

        value = sheet.cell(2, 1).value

        return f"Google Sheet Connected ✅<br><br>{value}"

    except Exception as e:
        return f"Error: {str(e)}"


@app.route("/mark-service/<row_id>")
def mark_service(row_id):

    try:

        row_number = int(row_id) + 1

        current_hours = sheet.cell(row_number, 3).value
        pc_no = sheet.cell(row_number, 1).value
        machine_id = sheet.cell(row_number, 2).value

        # Update Last Service Done At (Column D)
        sheet.update_cell(
            row_number,
            4,
            current_hours
        )

        # Service History tab
        history = client.open_by_key(
            "1EW68VrSfyzaD9UBhWORQe63QOwlz9QLfvQBWx1yWjzI"
        ).worksheet("Service History")

        from datetime import datetime

        history.append_row([
            datetime.now().strftime("%d-%b-%Y %H:%M"),
            pc_no,
            machine_id,
            current_hours
        ])

        send_telegram_message(
            f"✅ Service Recorded\n\n"
            f"{pc_no}\n"
            f"{machine_id}\n"
            f"Hours: {current_hours}"
        )

        return """
        <h2>Service Recorded Successfully</h2>
        <a href="/">Return to Dashboard</a>
        """

    except Exception as e:

        return f"Error: {str(e)}"

# ====================================
# TELEGRAM ALERT
# ====================================





@app.route("/send-alert")
def send_alert():

    data = scrape_hitrack()

    overdue = []

    due_soon = []

    for row in data:

        if row["Status"] == "OVERDUE":

            overdue.append(
                f"🔴 {row['PC No']} → "
                f"{row['Remaining Hours']} hrs"
            )

        elif row["Status"] == "DUE SOON":

            due_soon.append(
                f"🟡 {row['PC No']} → "
                f"{row['Remaining Hours']} hrs left"
            )

    message = (
        "🚨 MASTERS PC Service "
        "Monitor Dashboard\n\n"
    )

    if overdue:

        message += "OVERDUE:\n"

        message += "\n".join(overdue)

        message += "\n\n"

    if due_soon:

        message += "DUE SOON:\n"

        message += "\n".join(due_soon)

    if not overdue and not due_soon:

        message += (
            "✅ All machines "
            "operating normally"
        )

    send_telegram_message(message)

    return "Telegram alert sent successfully"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
