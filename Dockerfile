FROM python:3.11

ADD . /code
RUN cd /code && python -m pip install .
RUN rm -r /code

CMD ["gunicorn", "-w", "16", "-b", "0.0.0.0:8080", "ipsdataportal:create_app()"]
