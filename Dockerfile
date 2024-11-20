FROM python:3.8.6-slim
ENV PYTHONIOENCODING utf-8

# install gcc to be able to build packages - e.g. required by regex, dateparser, also required for pandas
RUN apt-get update && apt-get install -y build-essential

RUN pip install flake8

COPY requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

WORKDIR /code/

COPY /src /src/
COPY /tests /tests/
COPY /scripts /scripts/
COPY flake8.cfg /flake8.cfg
COPY deploy.sh /deploy.sh

CMD ["python", "-u", "/code/src/component.py"]
