FROM python:3.10

RUN mkdir /root/updater

WORKDIR /root/updater

COPY Pipfile Pipfile.lock updater.py ./

RUN pip install pipenv

RUN pipenv install --system --deploy --dev

EXPOSE 5001

ENTRYPOINT ["python", "updater.py", "--host", "server-container", "--port", "5000"]
