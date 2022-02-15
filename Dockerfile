FROM python:3.9.10-bullseye
LABEL maintainer="Ishan Karmakar"
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py", "prod"]
