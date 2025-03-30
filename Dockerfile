<<<<<<< HEAD
FROM python:3.13-slim
=======
FROM python:3.11-slim
>>>>>>> 8f1dfe4 (Setup)

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

<<<<<<< HEAD
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
=======
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

>>>>>>> 8f1dfe4 (Setup)
