FROM python:3.11-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY en_core_web_sm-3.8.0.tar.gz ./
RUN pip install --no-cache-dir ./en_core_web_sm-3.8.0.tar.gz
COPY . .
CMD [ "python", "./app.py" ]
