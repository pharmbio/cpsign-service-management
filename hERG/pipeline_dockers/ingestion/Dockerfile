FROM python:3.5.6-slim

RUN pip3.5 install pymysql jinja2 pandas

ADD data_preparation.py /home/
ADD parameter_file_preparation.py /home/
ADD params /home/params

WORKDIR /home