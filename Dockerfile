# build
FROM node:11.12.0-alpine as build-vue
WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
COPY ./client/package*.json ./
RUN npm config set registry http://`/sbin/ip route|awk '/default/ { print $3 }'`:8081/repository/npm
RUN npm install --verbose
COPY ./client .
RUN npm run build

# production
FROM nginx:stable-alpine as production
ENV PIP_CONFIG_FILE ~/pip.conf
WORKDIR /app
# https://github.com/sonatype-nexus-community/nexus-repository-apk
# If you haven't already, edit the Apline file located at /etc/apk/repositories to use your
# apk-proxy (i.e. add http://localhost:8081/repository/apk-proxy/ and comment out or delete
# the other remote repo locations).
RUN apk update && apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
COPY --from=build-vue /app/dist /usr/share/nginx/html
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./server/requirements.txt ./
COPY ./pip/pip.conf /tmp
RUN cat /tmp/pip.conf | sed -e "s/localhost/`/sbin/ip route|awk '/default/ { print $3 }'`/g" > ~/pip.conf

RUN pip install -r requirements.txt
RUN pip install gunicorn
COPY ./server .
CMD gunicorn -b 0.0.0.0:5000 app:app --daemon && \
      sed -i -e 's/$PORT/'"$PORT"'/g' /etc/nginx/conf.d/default.conf && \
      nginx -g 'daemon off;'