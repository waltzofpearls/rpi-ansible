FROM arm32v7/python:3.7.12-slim-buster
RUN apt-get update; \
    apt-get install -y --no-install-recommends \
        g++ \
        make \
        zlib1g-dev \
        libjpeg-dev \
        ; \
    rm -rf /var/lib/apt/lists/*
WORKDIR /reckon
COPY model/requirements.txt model/requirements.txt
RUN pip install --no-cache-dir -r model/requirements.txt
RUN pip install pystan==2.19.1.1
RUN pip install prophet==1.0.1
COPY . .
CMD ["./reckon"]
