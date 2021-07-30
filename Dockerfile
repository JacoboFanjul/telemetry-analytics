FROM python:3.7-alpine

WORKDIR /konnektbox-telemetry
ENV PYTHONUNBUFFERED=1

RUN apk update && apk upgrade && apk add --no-cache libc6-compat gcc musl-dev linux-headers
COPY requirements.txt ./
RUN python3 -m pip install -r requirements.txt
COPY . .

ENTRYPOINT [ "python3", "app.py" ]
