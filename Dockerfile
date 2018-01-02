from alpine:latest

WORKDIR /app

COPY . .

RUN apk update
RUN apk add python3
RUN pip3 install -r requirements.txt

ENTRYPOINT python3 geolocator.py
