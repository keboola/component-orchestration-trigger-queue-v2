FROM python:3.12-slim
ENV PYTHONIOENCODING=utf-8

RUN pip install flake8
COPY flake8.cfg /code/flake8.cfg

COPY requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt

COPY /src /code/src/
COPY /tests /code/tests/
COPY /scripts /code/scripts/
COPY deploy.sh /code/deploy.sh

WORKDIR /code/
CMD ["python", "-u", "/src/component.py"]
