"""
🚨 Waze Baleset Monitor – Budapest régió
GitHub Actions self-loop, percenként fut
Token refresh: külön workflow 10 percenként
"""

import os
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header

# ─────────────────────────────────────────────
# KONFIGURÁCIÓ
# ─────────────────────────────────────────────
EMAIL_KULDO   = os.environ["EMAIL_KULDO"]
EMAIL_JELSZO  = os.environ["EMAIL_JELSZO"]
EMAIL_CIMZETT = os.environ["EMAIL_CIMZETT"]
# Token betöltése fájlból vagy environment változóból
def load_token():
    if os.path.exists("waze_token.txt"):
        with open("waze_token.txt", "r") as f:
            t = f.read().strip()
            if t:
                return t
    return os.environ.get("WAZE_TOKEN", "")

WAZE_TOKEN = load_token()

REGION_TOP    = 47.78
REGION_BOTTOM = 47.22
REGION_LEFT   = 18.68
REGION_RIGHT  = 19.41

ALLAPOT_FILE  = "waze_allapot.json"

# ─────────────────────────────────────────────
# ÁLLAPOT KEZELÉS
# ─────────────────────────────────────────────
def load_allapot():
    if os.path.exists(ALLAPOT_FILE):
        try:
            with open(ALLAPOT_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"seen": []}

def save_allapot(allapot):
    with open(ALLAPOT_FILE, "w") as f:
        json.dump(allapot, f, indent=2)

# ─────────────────────────────────────────────
# WAZE LEKÉRDEZÉS
# ─────────────────────────────────────────────
def fetch_waze():
    if not WAZE_TOKEN:
        print("[HIBA] WAZE_TOKEN hiányzik!")
        return []

    url = (
        "https://www.waze.com/live-map/api/georss"
        "?top=%.5f&bottom=%.5f&left=%.5f&right=%.5f&env=row&types=alerts,traffic"
        % (REGION_TOP, REGION_BOTTOM, REGION_LEFT, REGION_RIGHT)
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "Referer": "https://www.waze.com/hu/live-map",
        "Accept": "application/json, text/plain, */*",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        "sec-ch-ua-mobile": "?0",
        "X-Recaptcha-Token": WAZE_TOKEN,
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        print("[WAZE] Status: %d" % r.status_code)
        if r.status_code == 200:
            data = r.json()
            alerts = data.get("alerts", [])
            print("[WAZE] Alertek száma: %d" % len(alerts))
            return alerts
        else:
            print("[WAZE] Hiba: %d" % r.status_code)
            return []
    except Exception as e:
        print("[WAZE] Kivétel: %s" % str(e))
        return []

# ─────────────────────────────────────────────
# EMAIL KÜLDÉS
# ─────────────────────────────────────────────
def send_email(alert):
    city    = alert.get("city", "") or "Budapest"
    street  = alert.get("street", "") or "Ismeretlen út"
    atype   = alert.get("type", "ACCIDENT")
    subtype = alert.get("subtype", "")
    loc     = alert.get("location", {})
    lat     = loc.get("y", 0)
    lon     = loc.get("x", 0)

    gmaps = "https://www.google.com/maps/search/?api=1&query=%.5f,%.5f" % (lat, lon)
    waze  = "https://www.waze.com/ul?ll=%.5f,%.5f&navigate=yes" % (lat, lon)
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    subject = "BALESET [WAZE]: %s, %s" % (city, street)

    body = (
        "<div style='font-family:sans-serif;line-height:1.6;max-width:640px;'>"
        "<h2 style='color:#d93025;'>🚨 Baleseti Riasztás – WAZE</h2>"
        "<table style='border-collapse:collapse;width:100%;'>"
        "<tr><td style='padding:4px 8px;font-weight:bold;width:160px;'>Forrás:</td><td>🟦 WAZE</td></tr>"
        "<tr style='background:#f8f8f8;'><td style='padding:4px 8px;font-weight:bold;'>Település:</td><td>%s</td></tr>"
        "<tr><td style='padding:4px 8px;font-weight:bold;'>Helyszín:</td><td>%s</td></tr>"
        "<tr style='background:#f8f8f8;'><td style='padding:4px 8px;font-weight:bold;'>Típus:</td><td>%s</td></tr>"
        "<tr><td style='padding:4px 8px;font-weight:bold;'>Leírás:</td><td>%s</td></tr>"
        "<tr style='background:#f8f8f8;'><td style='padding:4px 8px;font-weight:bold;'>GPS:</td><td>%.5f, %.5f</td></tr>"
        "</table><br>"
        "<a href='%s' style='background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;font-weight:bold;margin-right:10px;'>Waze-ben nyit</a>"
        "<a href='%s' style='background:#34a853;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;font-weight:bold;'>Google Maps</a>"
        "<hr><small style='color:#888;'>Időpont: %s</small></div>"
    ) % (city, street, atype, subtype or "-", lat, lon, waze, gmaps, ts)

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"]    = "Waze Monitor <" + EMAIL_KULDO + ">"
    msg["To"]      = EMAIL_CIMZETT

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_KULDO, EMAIL_JELSZO)
            server.sendmail(EMAIL_KULDO, EMAIL_CIMZETT, msg.as_string())
        print("  [EMAIL] Elküldve: %s, %s" % (city, street))
        return True
    except Exception as e:
        print("  [EMAIL HIBA] %s" % str(e))
        return False

# ─────────────────────────────────────────────
# FŐ LOGIKA
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("WAZE MONITOR – %s" % datetime.now().strftime("%H:%M:%S"))
    print("=" * 50)

    allapot = load_allapot()
    seen    = set(allapot.get("seen", []))

    alerts = fetch_waze()
    uj     = 0

    for a in alerts:
        atype = a.get("type", "")
        if atype != "ACCIDENT":
            continue

        aid = a.get("uuid") or a.get("id") or ""
        if not aid or aid in seen:
            continue

        print("ÚJ BALESET: %s, %s" % (a.get("city", "?"), a.get("street", "?")))
        send_email(a)
        seen.add(aid)
        uj += 1

    # Max 500 ID tárolása
    allapot["seen"] = list(seen)[-500:]
    save_allapot(allapot)

    print("Összesen: %d alert, %d új baleset" % (len(alerts), uj))

if __name__ == "__main__":
    main()
