FROM nvcr.io/nvidia/l4t-base:r32.5.0

WORKDIR /konnektbox-telemetry
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc python3-pip
COPY tegrastats requirements.txt ./
RUN python3 -m pip install -r requirements.txt
COPY . .

ENTRYPOINT [ "python3", "app.py" ]
