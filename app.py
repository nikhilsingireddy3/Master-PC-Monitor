import requests

def scrape_hitrack():
    url = "https://hyundai-ce.live/MachinePerformanceReport/MachinePerformanceReportGridView"

    headers = {
        "Cookie": """c1=CnFrwVPQYlTyNH9CMCopuRURz1ZIKC3E1MPTTQQUCVMV4WzasMge7Au/gOSBVK4c; 
        JSESSIONID=55A064410BD1AF4E81B3D2339751CC5C; 
        AWSELB=A1374585027AECE6E1999905DCA119937B811FE2EE88AA3EFCCA033EC939D5B0EA7BDC3D0BE9A5B4AE74345DABB477D8276BF37CF45BF403145C98ABE9ED27381A31363F77B367F39FD51E30017E26C26EF095D780""",
        "User-Agent": "Mozilla/5.0"
    }

    machines = {
        "HYNDN635EE0069980": 43261,
        # add remaining machines here
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

        response = requests.get(url, params=params, headers=headers)
        data = response.json().get("data", [])

        if not data:
            continue

        for row in reversed(data):
            hm = row.get("HourMeter")
            if hm:
                h, m = hm.split(":")
                results[machine_id] = round(float(h) + float(m)/60, 2)
                break

    return results