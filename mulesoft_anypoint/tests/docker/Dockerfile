FROM python:alpine3.7
COPY . /app
COPY ./apis /app/apis
COPY ./conn_mock.py /app/conn_mock.py
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python ./mocked_service.py