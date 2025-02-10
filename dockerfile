FROM python:3.8

ADD hello.py .

RUN pip install pygame

CMD [ "python", "./hello.py" ]


