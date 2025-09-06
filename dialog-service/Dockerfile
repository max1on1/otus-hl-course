FROM python:alpine as builder

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:alpine

WORKDIR /app

COPY . .

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
