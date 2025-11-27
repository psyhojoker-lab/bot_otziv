from sheets import get_unsent_feedbacks, get_unique_categories

if __name__ == "__main__":
    print("Получаем отзывы, которые ещё не отправлены в Telegram...")
    feedbacks = get_unsent_feedbacks()
    print(f"Найдено {len(feedbacks)} отзывов.")

    print("\nУникальные категории (где есть непрочитанные отзывы):")
    categories = get_unique_categories()
    for i, cat in enumerate(categories):
        print(f"{i} — {cat}")