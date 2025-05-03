FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]