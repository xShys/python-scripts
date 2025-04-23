import pandas as pd
import requests
import datetime
import smtplib
from email.message import EmailMessage
from concurrent.futures import ThreadPoolExecutor

# Configurazione email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = ""  # Sostituisci con la tua email da cui inviare il report
EMAIL_PASSWORD = ""  # Sostituisci con la password dell'account email da cui invii il report
EMAIL_RECEIVER = ""  # Sostituisci con l'email a cui vuoi inviare il report

def fetch_bitcoin_data_for_year(year):
    API_URL = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=EUR&limit=365&toTs={int(datetime.datetime(year, 12, 31).timestamp())}"
    # print(API_URL)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(API_URL, headers=headers)
    if response.status_code != 200:
        print(f"Errore nell'accesso all'API per l'anno {year}: {response.status_code}")
        return None
    
    data = response.json()
    if "Data" not in data["Data"]:
        print(f"Errore: la risposta dell'API per l'anno {year} non contiene dati validi.")
        return None
    
    prices = data["Data"]["Data"]
    
    # Creare un DataFrame con la data e il prezzo medio (high + low) / 2
    df = pd.DataFrame(prices)
    df["Date"] = pd.to_datetime(df["time"], unit='s')
    df["price"] = (df["high"] + df["low"]) / 2
    df["Day"] = df["Date"].dt.day_name()
    df["Month"] = df["Date"].dt.month
    df["Season"] = df["Month"].map({
        12: "Inverno", 1: "Inverno", 2: "Inverno",
        3: "Primavera", 4: "Primavera", 5: "Primavera",
        6: "Estate", 7: "Estate", 8: "Estate",
        9: "Autunno", 10: "Autunno", 11: "Autunno"
    })
    
    return df

# Scarica i dati storici di Bitcoin per più anni in parallelo
def fetch_bitcoin_data():
    years = list(range(2011, datetime.datetime.now().year + 1))
    with ThreadPoolExecutor(max_workers=5) as executor:  # Limitiamo a 5 richieste parallele
        results = list(executor.map(fetch_bitcoin_data_for_year, years))
    
    # Unisci tutti i dati in un unico DataFrame
    df = pd.concat([r for r in results if r is not None], ignore_index=True)
    df.sort_values(by="Date", inplace=True)
    return df

def analyze_best_days(df):
    """Analizza i giorni migliori per ogni stagione."""
    if df is None:
        print("Errore: nessun dato disponibile per l'analisi.")
        return None
    
    best_days = {}
    price_stats = []
    for season in ["Inverno", "Primavera", "Estate", "Autunno"]:
        df_season = df[df["Season"] == season]
        best_day = df_season.groupby("Day")["price"].mean().idxmin()
        if best_day == "Monday":
            best_day = "Lunedì"
        elif best_day == "Tuesday":
            best_day = "Martedì"
        elif best_day == "Wednesday":
            best_day = "Mercoledì"
        elif best_day == "Thursday":
            best_day = "Giovedì"
        elif best_day == "Friday":
            best_day = "Venerdì"
        elif best_day == "Saturday":
            best_day = "Sabato"
        elif best_day == "Sunday":
            best_day = "Domenica"
        best_days[season] = best_day
    
    return best_days

def send_email(best_days, parm1, parm2, onError):
    if onError:
        report_text = (f"Si è verificato un errore nello script: {parm1}.\n\n")
    else:
        if best_days is None:
            report_text = "Nessun dato da inviare. Verifica l'API."
        else:
            # Creazione del testo dell'email se tutto ok
            report_text = "Ecco il report mensile sui giorni statisticamente migliori in base alla stagione per acquistare in modo ricorrente Bitcoin:\n\n"
            for season, day in best_days.items():
                report_text += f"{season}: {day}\n"
    
    msg = EmailMessage()
    msg["Subject"] = "Bitcoin Report Mensile"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content(report_text)
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    
    print("Email inviata con successo!")

if __name__ == "__main__":
    try:
        print("Scaricamento dati Bitcoin...")
        df = fetch_bitcoin_data()
        if df is not None:
            print("Analisi in corso...")
            best_days = analyze_best_days(df)

            print("Invio email...")
            send_email(best_days, '', '', False)
            print("Analisi completata!")
        else:
            print("Nessun dato disponibile per l'analisi.")
            send_email(None, "Nessun dato disponibile per l'analisi.", "", True)
            print("Email di errore inviata.")
    except Exception as err:
        print(f"Si è verificato un errore: {err}")
        send_email(None, err, "", True)
        print("Email di errore inviata.")
