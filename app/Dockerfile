FROM python:3.11-bookworm

COPY ./setup.py /app/setup.py

WORKDIR /app

RUN \
  mkdir -p src && \
  pip install -U pip && \
  pip install -e .

COPY ./ /app/
