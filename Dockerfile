FROM python:3.12-slim

WORKDIR /app

# install deps first (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code + static assets
COPY app.py .
COPY demo.html .

EXPOSE 8080

CMD ["python", "app.py"]
