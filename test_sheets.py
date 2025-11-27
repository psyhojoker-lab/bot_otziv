import gspread
from google.oauth2.service_account import Credentials

# Вставьте ID таблицы напрямую
SHEET_ID = "1l2zlOyJhrZOLC-Dj6xt8iKb9_I47b-p9jSgHwjxM1eU"
CREDENTIALS_FILE = "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

try:
    sheet = gc.open_by_key(SHEET_ID).worksheet("ReviewsWB")
    print("✅ Успешно подключились к листу 'ReviewsWB'")

    rows = sheet.get_all_records(expected_headers=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])
    print(f"Всего строк: {len(rows)}")

    if rows:
        print("Первая строка:", rows[0])
except Exception as e:
    print("❌ Ошибка:", e)