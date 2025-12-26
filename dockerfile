FROM python:3.12-slim

# Working directory
WORKDIR /usr/src/app

# Kopiýala ähli faýllary
COPY . .

# Talaplary gur
RUN pip install --no-cache-dir -r requirements.txt

# Actor işledýän faýl
CMD ["python", "main.py"]
