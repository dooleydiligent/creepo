FROM debian:12-slim

RUN apt update -y && \
  apt install -y python3 python3-venv

ADD setup.* /app/
ADD README.md /app/
ADD MANIFEST.in /app/

#ADD client/* /app/client/
ADD tests/test_creepo.py /app/tests/
ADD creepo/* /app/creepo/

ENV BOTTLE_APP=creepo
ENV BOTTLE_ENV=development

WORKDIR /app

RUN python3 -m venv venv

RUN . venv/bin/activate && pip install '.[test]' WebTest pytest-cov
RUN . venv/bin/activate && coverage run -m pytest 
RUN . venv/bin/activate && coverage report && coverage html

RUN . venv/bin/activate && pip install -e .

ENTRYPOINT ["python3", "creepo"]