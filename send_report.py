import os
import sys
import smtplib
from datetime import date
from email.mime.text import MIMEText
from dotenv import load_dotenv

from fetch_jobs import get_jobs
from filter_jobs import evaluate_jobs

load_dotenv()


def build_html(jobs, oceny):
    pasujace = []
    for ocena in oceny:
        if ocena["pasuje"]:
            job = jobs[ocena["id"]]
            pasujace.append((job, ocena))

    if not pasujace:
        return """
        <html>
        <body>
            <p>Dziś nie znaleziono żadnych pasujących ofert pracy.</p>
        </body>
        </html>
        """

    items_html = ""
    for job, ocena in pasujace:
        title = job["title"]
        company = job.get("company", {}).get("display_name", "?")
        powod = ocena["powod"]
        link = job["redirect_url"]
        items_html += f"""
        <li>
            <strong>{title}</strong> - {company}<br>
            Powód: {powod}<br>
            <a href="{link}">{link}</a>
        </li>
        <br>
        """

    return f"""
    <html>
    <body>
        <p>Dzisiejsze pasujące oferty pracy:</p>
        <ul>
            {items_html}
        </ul>
    </body>
    </html>
    """


def send_email(html_body, subject):
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_APP_PASSWORD")

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = email_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_address, email_password)
        server.sendmail(email_address, email_address, msg.as_string())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    jobs = get_jobs()
    oceny = evaluate_jobs(jobs)
    html_body = build_html(jobs, oceny)
    subject = "Raport ofert pracy - " + date.today().strftime("%d.%m.%Y")

    try:
        send_email(html_body, subject)
        print("Mail wysłany poprawnie.")
    except Exception as e:
        print(f"BŁĄD PRZY WYSYŁCE MAILA: {e}")
