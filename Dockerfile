FROM python:latest

RUN pip3 install mysql-connector-python
RUN pip3 install requests pytz pyhs100
COPY . /

CMD ["python", "/stream.py"]