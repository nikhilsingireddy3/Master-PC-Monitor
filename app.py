from flask import Flask, render_template_string
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
# ALERT ROUTE
# ====================================


@app.route('/send-alert')
def send_alert():

    data = scrape_hitrack()

    overdue = []
    due_soon = []

    for row in data:

        if row['Status'] == 'OVERDUE':

            overdue.append(
                f"🔴 {row['PC No']} → {row['Remaining Hours']} hrs"
            )

        elif row['Status'] == 'DUE SOON':

            due_soon.append(
                f"🟡 {row['PC No']} → {row['Remaining Hours']} hrs left"
            )

    message = "🚨 HD Fleet Alert\n\n"

    if overdue:

        message += "OVERDUE:\n"
        message += "\n".join(overdue)
        message += "\n\n"

    if due_soon:

        message += "DUE SOON:\n"
        message += "\n".join(due_soon)
        message += "\n\n"

    if not overdue and not due_soon:

        message += "✅ All machines operating normally"

    send_telegram_message(message)

    send_email(
        "HD Fleet Alert",
        message
    )

    return "Telegram and Email alerts sent successfully"


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
