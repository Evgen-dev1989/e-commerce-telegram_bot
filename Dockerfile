
FROM python:3.12-slim


WORKDIR /app


RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*


RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*


RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` \
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app


EXPOSE 8000


CMD ["python", "main.py"]
