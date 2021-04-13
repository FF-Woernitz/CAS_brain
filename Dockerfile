FROM python:3-alpine

WORKDIR /opt/brain
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD [ "python3", "-u", "./main.py" ]
