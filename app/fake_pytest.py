# -*- coding: utf-8 -*-

import shutil

# ANSI escape-коды для цветов
GREEN = "\033[92m"  # Ярко-зеленый для успешных тестов
YELLOW = "\033[93m"  # Желтый для заголовков и сводки
ENDC = "\033[0m"  # Код для сброса цвета к значению по умолчанию

# --- Начало вывода ---

# Получаем ширину терминала, по умолчанию 80, если не удается определить
try:
    width = shutil.get_terminal_size().columns
except OSError:
    width = 80

# Заголовок сессии
print(f"{GREEN}❯ pytest{ENDC}")
title = " test session starts "
print(title.center(width, "="))


# Информация о системе и плагинах (оставляем цветом по умолчанию)
print("platform darwin -- Python 3.12.10, pytest-8.4.1, pluggy-1.6.0")
print("rootdir: /Users/retrobanner/WorkBench/УИР/app")
print("plugins: anyio-4.9.0, asyncio-1.0.0")
print("asyncio: mode=Mode.STRICT")
print("collected 47 items\n")

# Прогресс выполнения тестов
# Точки и проценты окрашиваем в зеленый


def print_progress_line(path: str, dots: str, percent: str):
    """Выводит строку прогресса, выравнивая проценты по правому краю."""
    # Рассчитываем количество пробелов для выравнивания.
    # 1 - это пробел между путем и точками.
    padding_len = width - len(path) - 1 - len(dots) - len(percent)
    padding = " " * max(0, padding_len)

    # Формируем и выводим строку
    print(f"{path} {GREEN}{dots}{padding}{percent}{ENDC}")


print_progress_line("tests/features/test_tables.py", "............", "[ 25%]")
print_progress_line(
    "tests/features/test_users.py", "...............................", "[ 91%]"
)
print_progress_line("tests/test_services.py", "....", "[100%]")

print()  # Пустая строка для отступа

# Финальная сводка
raw_summary_text = "47 passed in 18.94s"
summary_text = f" {raw_summary_text} "
total_padding = width - len(summary_text)
left_padding = "=" * (total_padding // 2)
right_padding = "=" * (total_padding - (total_padding // 2))

print(f"{GREEN}{left_padding}{summary_text}{right_padding}{ENDC}")
