import gspread
from google.oauth2.service_account import Credentials
from config import CREDENTIALS_FILE, GOOGLE_SHEET_ID

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# sheets.py

def update_feedback_reply(feedback_id, manual_reply=None, ai_reply=None):
    """
    Обновляет строку в таблице по feedbackId
    :param feedback_id: ID отзыва (столбец A)
    :param manual_reply: текст ручного ответа (столбец I)
    :param ai_reply: текст или флаг генерации (столбец J)
    """
    sheet = get_sheet()
    # Находим строку по feedbackId (столбец 1)
    cell = sheet.find(str(feedback_id), in_column=1)
    row_num = cell.row

    # Обновляем столбцы:
    # H — wbAnswered = TRUE
    # I — manualReply
    # J — aiReply
    updates = []
    if manual_reply is not None:
        updates.append((row_num, 9, manual_reply))  # I = 9
    if ai_reply is not None:
        updates.append((row_num, 10, ai_reply))  # J = 10
    updates.append((row_num, 8, 'TRUE'))  # H = 8

    for row, col, value in updates:
        sheet.update_cell(row, col, value)

    print(f"✅ Отзыв {feedback_id} обновлён: manualReply={manual_reply}, aiReply={ai_reply}")

def get_sheet():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(GOOGLE_SHEET_ID).worksheet("ReviewsWB")
    return sheet

def get_unsent_feedbacks():
    sheet = get_sheet()
    # Указываем числовые заголовки
    rows = sheet.get_all_records(expected_headers=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])

    # Фильтруем: F (6) — не пустой, L (12) — FALSE
    return [
        r for r in rows
        if r.get('6') and r.get('12') == 'FALSE'  # text и sentToTelegram
    ]

def get_unique_categories():
    sheet = get_sheet()
    rows = sheet.get_all_records(expected_headers=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])
    # Фильтруем: F (6) — не пустой, L (12) — FALSE
    filtered = [r for r in rows if r.get('6') and r.get('12') == 'FALSE']
    categories = list(set(r['4'] for r in filtered if r.get('4')))  # subjectName (D)
    categories.sort()
    return categories