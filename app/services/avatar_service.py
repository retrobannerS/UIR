import hashlib
import os
from PIL import Image, ImageDraw, ImageFont
import uuid

# Убедимся, что директория для аватаров существует
AVATAR_DIR = "uploads/avatars"


def get_font(size):
    """
    Пытается найти системный шрифт. Возвращает шрифт по умолчанию, если не найден.
    """
    # Сначала ищем жирные шрифты
    bold_font_paths = [
        "arialbd.ttf",  # Windows Bold
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS Bold
        "Helvetica-Bold.ttc",  # macOS Bold
        "LiberationSans-Bold.ttf",  # Linux Bold
    ]
    # Затем обычные, если жирные не найдены
    regular_font_paths = [
        "arial.ttf",  # Windows
        "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
        "Helvetica.ttc",  # macOS
        "LiberationSans-Regular.ttf",  # Linux
    ]

    for font_path in bold_font_paths + regular_font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            continue

    # Если ничего не найдено, используем шрифт по умолчанию от Pillow.
    # Он будет маленьким, так как параметр size игнорируется.
    return ImageFont.load_default()


def generate_avatar(username: str) -> str:
    """
    Генерирует аватар для пользователя, сохраняет его и возвращает путь.
    """
    # 1. Генерация цвета на основе имени пользователя
    hash_object = hashlib.md5(username.encode())
    hex_dig = hash_object.hexdigest()
    # Берем первые 6 символов для цвета
    color = f"#{hex_dig[:6]}"

    # 2. Получение первой буквы и создание изображения
    letter = username[0].upper()
    image = Image.new("RGB", (200, 200), color=color)
    draw = ImageDraw.Draw(image)

    # 3. Написание буквы на изображении
    font = get_font(144)  # Уменьшаем размер до 90% и делаем жирным

    # Используем anchor="mm" для идеального центрирования.
    try:
        draw.text(
            (100, 100),  # Центр изображения
            letter,
            fill="white",
            font=font,
            anchor="mm",
        )
    except (TypeError, AttributeError):
        # Фоллбэк, если шрифт не поддерживает anchor (например, дефолтный шрифт).
        # Этот метод центрирования менее точен и может использовать устаревшие функции.
        width, height = draw.textsize(letter, font=font)
        x = (200 - width) / 2
        y = (200 - height) / 2
        draw.text((x, y), letter, fill="white", font=font)

    # 4. Сохранение файла с уникальным именем
    avatar_filename = f"{uuid.uuid4()}.png"
    avatar_path = os.path.join(AVATAR_DIR, avatar_filename)

    # Убедимся, что директория существует прямо перед сохранением
    os.makedirs(os.path.dirname(avatar_path), exist_ok=True)

    image.save(avatar_path)

    # Возвращаем URL-путь для доступа через веб
    return f"/{avatar_path.replace(os.path.sep, '/')}"
