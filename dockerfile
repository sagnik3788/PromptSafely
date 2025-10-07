FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

CMD ["uv", "run", "gunicorn", "api.api:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000"]
