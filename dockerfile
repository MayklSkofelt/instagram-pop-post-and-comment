FROM apify/actor-python:3.12

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
