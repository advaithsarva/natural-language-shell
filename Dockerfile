FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nlpcli.py test_nlpcli.py ./

# Nothing here needs root, and the container is where any approved command runs.
RUN useradd --create-home app
USER app

ENTRYPOINT ["python", "nlpcli.py"]
