FROM python:3.8

ADD database .

RUN pip install pygame sqlite3

CMD [ "python", "./database.py" ]
