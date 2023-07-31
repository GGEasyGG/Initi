FROM python:3.10

RUN mkdir /root/server

WORKDIR /root/server

COPY Pipfile Pipfile.lock server.py ./

RUN pip install pipenv

RUN pipenv install --system --deploy --dev

EXPOSE 5000

ENTRYPOINT ["python", "server.py", "--host", "0.0.0.0", "--port", "5000"]
