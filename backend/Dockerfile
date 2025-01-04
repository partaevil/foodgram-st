FROM python:3.12.7

WORKDIR /backend

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт
EXPOSE 8000

# Команда для запуска сервера
# ATTENTION: using for now local db.sqlite3
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]
