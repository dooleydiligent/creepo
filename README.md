### Creepo
  - a caching, multi-format repository / proxy for small network usage

### Motivation
Once in a while you find yourself on a network put together by unsupervised children.  In such case
you may find a spurrious proxy or other blocker which prevents your team from actually producing any code because you can't reach the outside world.

These are the times that you realize that you must be slightly smarter than the machines that you serve.

And always you must have already forgotten more than your network engineer will ever know.

By default, Creepo doesn't actually cache anything.  That would be creepy.  And potentially unsafe.

Instead, Creepo is intended to be configured with a global proxy to act as a sort of gateway to various artifact repositories, either inside or outside of the local network.

- Use Creepo behind a corporate firewall to proxy well used upstream repositories, such as npm, pip, maven, composer, and docker.

- Use Creepo to take a "snapshot" of build dependencies for later analysis, such as license query or vulnerability scans.

- Use Creepo to facilitate an "air-gapped" installation of some other application.

### Install

### Clone the repository

- [Visit the repository](https://github.com/dooleydiligent/creepo)
- [PyDoc](https://dooleydiligent.github.io/creepo/index.html) **(needs work)**
- [Unit Test Coverage](https://dooleydiligent.github.io/creepo/htmlcov/index.html) 

```
git clone git@github.com:dooleydiligent/creepo.git
cd creepo
```
### Build in docker

```
docker build . -t creepo
```
### Run in docker

```
docker run --rm --name creepo --net host creepo
```

### Use ssl by default

```
See https://gist.github.com/webknjaz/56cfb9f28a05017ea465982328b71d10 for some background

# Get the client certificate from the running container
docker cp creepo:/app/client.pem .

```

### Coverage report

See the coverage report [in the running docker image](http://localhost:4443/coverage/index.html)

### Create a virtualenv and activate it
- Just do it with python 3.  Eventually you don't notice the pain

```
python3 -m venv venv
. venv/bin/activate
```

### Install Creepo
```
pip install --upgrade pip poetry .
poetry install -C creepo --no-interaction --no-root
```

### Run
```
python creepo 
```

### Generate coverage report
```
coverage run -m pytest
coverage html --omit="*/test*"
```

### Generate pydoc

```
python -m pydoc -w creepo
mv creepo.html index.html
python -m pydoc -w creepo/*.py
sed -i 's,"creepo\.,",g' index.html
mv __init__.html __main__.html
```

### Use it as a Maven proxy
```
# You must first trust the creep
# Find your JAVA_HOME
# import the client (ca) certificate
# This assumes you are running in ubuntu 22.04+.  ymmv

# Delete a previous certificate
sudo keytool -delete -alias creepo \
  -keystore  $(dirname $(dirname $(readlink -f $(which java))))/lib/security/cacerts \
  -storepass changeit -noprompt

# Add the new certificate
sudo keytool -import -alias creepo -file client.pem \
    -keystore  $(dirname $(dirname $(readlink -f $(which java))))/lib/security/cacerts \
    -storepass changeit -noprompt

mvn dependency:get \
    -DrepoUrl=https://localhost:4443/m2/ \
    -Dartifact=org.sonatype.nexus.plugins:nexus-plugins:2.12.1-01 \
    -s ./demo/mvn/settings.xml
```

### Use it as an npm proxy
```
npm install --cafile client.pem --registry=https://localhost:4443/npm/ http-server

# debug with
NODE_DEBUG=tls,https,http npm -ddd install --verbose --cafile client.pem --registry=https://localhost:4443/npm/
```

### Use it as a pip proxy 
```
pip install . -i https://localhost:4443/pip --trusted-host localhost
```

### Use it as a composer proxy
- First install composer in some project.

Assumes you already have composer installed.  If not see [the documentation](https://packagist.org/)
```
cd demo/composer
composer install
```
### Use it as a docker proxy
- This assumes you have configured an upstream mirror.  We cannot (yet) proxy registry-1.docker.io, but plan to in the future.


Using this [configuration](./config.yml)
```
# 
# docker:
#     registry: 'https://docker.tuscawilla.local:32000'
#     cacert: '/home/lane/git/creepo/demo/docker/docker.tuscawilla.local.crt'
#     credentials:
#         username: 'docker'
#         password: 'password'

docker pull localhost:4443/pravega/pravega

Using default tag: latest
latest: Pulling from pravega/pravega
a0d0a0d46f8b: Pull complete 
083e16b808d4: Pull complete 
16cb052eff29: Pull complete 
7b7fe9910a72: Pull complete 
a847de4745a5: Pull complete 
08b71253a7a0: Downloading [>                                                  ]  1.622MB/196MB
aa509fd13681: Download complete 
3731688bad93: Download complete 

```
