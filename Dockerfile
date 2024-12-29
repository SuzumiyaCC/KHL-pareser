# Используем базовый образ с установленным Python
FROM python:3.12-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    wget \
    cron \
    unzip \
    gnupg2 && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    apt-get clean

# Установка библиотек Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем скрипты и Flask-приложение в контейнер
COPY scripts /app/scripts
COPY app.py /app/
COPY templates /app/templates

# Устанавливаем рабочую директорию
WORKDIR /app

# Настройка cron для запуска парсера каждый час
RUN echo "0 * * * * root /usr/local/bin/python3.12 /app/scripts/parser.py >> /var/log/cron.log 2>&1" > /etc/cron.d/parser-cron

# Даем права на выполнение cron-файла
RUN chmod 0644 /etc/cron.d/parser-cron

# Создаем лог-файл для cron и даем права на запись
RUN touch /var/log/cron.log && chmod 666 /var/log/cron.log

# Даем права на выполнение скрипта парсера
RUN chmod +x /app/scripts/parser.py

# Запуск cron и Flask-приложения
CMD cron && flask run --host=0.0.0.0 --port=5000