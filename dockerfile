FROM python:3.8

ADD database.py .

#RUN pip install pygame

CMD [ "python", "./database.py" ]