ARG DOCKER_MIRROR=docker.io
FROM $DOCKER_MIRROR/library/python:3.10-slim

ADD README.md /app/
ADD LICENSE /app/
ADD pyproject.toml /app/
ADD tests/* /app/tests/
ADD creepo/*   /app/creepo/
#ADD tuscawilla-ca.crt /caRoot.crt

ENV CREEPO_APP=creepo
ENV CREEPO_ENV=development
ENV HOME=/app
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin

ARG USERNAME=creepo
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN addgroup --gid $USER_GID $USERNAME 
RUN adduser --uid $USER_UID $USERNAME --system --ingroup $USERNAME

RUN chown $USERNAME: /app

WORKDIR /app

USER $USERNAME
#ARG PIP_MIRROR=https://pypi.org/simple

#RUN pip config --user set global.index-url $PIP_MIRROR
#RUN pip config --user set global.cert /caRoot.crt
RUN pip install --upgrade pip trustme .
RUN python -m trustme
RUN coverage run -m pytest

RUN coverage html --omit="*/test*"

ENTRYPOINT ["python3", "creepo"]

# https://stackoverflow.com/questions/18525152/git-clone-and-checkout-in-a-single-command
