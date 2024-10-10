# Используем базовый образ с установленным Python
FROM python:3.12-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    wget \
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

# Копируем скрипты в контейнер
COPY scripts /app/scripts
WORKDIR /app/scripts

# Запускаем скрипт
CMD ["sleep", "infinity"]

