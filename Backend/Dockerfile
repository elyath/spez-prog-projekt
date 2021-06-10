FROM python:3

RUN pip install flask
RUN pip install pandas
RUN pip install matplotlib

WORKDIR /usr/src/app

ADD ./src/ /usr/src/app/

CMD ["python","-u","server.py" ]