FROM python:3.13

WORKDIR /app

# Устанавливаем poetry
RUN pip install poetry

# Копируем файлы poetry
COPY pyproject.toml poetry.lock* ./

# Создаем и активируем виртуальное окружение, устанавливаем зависимости
RUN poetry install --no-root --without dev

# Копируем остальной код
COPY . .

# Запускаем через poetry run или активируем окружение
CMD ["poetry", "run", "python", "bot.py"]