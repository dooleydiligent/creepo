### Creepo
  - a cachining multi-format repository proxy for small network usage

### Motivation
Once in a while you find yourself on a network put together by unsupervised children.  In such case
you may find a spurrious proxy or other blocker which prevents your team from actually producing any code because you can't reach the outside world.

These are the times that you realize that you must be slightly smarter than the machines that you serve.

And always you must have already forgotten more than your network engineer will ever know.

Use Creepo to cache well used upstream repositories, such as npm, pip, and maven.  More will follow shortly.

### Install

### clone the repository
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
### use ssl by default
```
See https://gist.github.com/webknjaz/56cfb9f28a05017ea465982328b71d10 for some background

# Get the client certificate from the running container
docker cp creepo:/app/client.pem .

# Update local ca-certificates
sudo cp client.pem /usr/local/share/ca-certificates/creepo.crt
sudo update-ca-certificates

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
pip install --upgrade pip .

```

### Run
```
export CREEPO_APP=creepo
export CREEPO_ENV=development

python creepo >creepo.log 2>&1
```

### Test
<<<<<<< HEAD
=======
```
pip install '.[test]'
```

### Run with coverage report
>>>>>>> 5586084 (feat: update npm example (#35))
```
coverage run -m pytest
```

<<<<<<< HEAD
### Run with coverage report
=======
### Use it as a Maven proxy repo
>>>>>>> 5586084 (feat: update npm example (#35))
```
coverage html --omit="*/test*"
```

### Use it as a Maven proxy repo
```
cd demo/mvn

mvn dependency:get \
    -DrepoUrl=https://localhost:4443/m2/ \
    -Dartifact=org.sonatype.nexus.plugins:nexus-plugins:2.12.1-01 \
    -s ./settings.xml
```

### Use it as an npm proxy repo
```
cd client
npm install --registry=http://localhost:5000/npm/
```

### Use it as a pip proxy repo
```
pip install -e . -i http://localhost:5000/pip/
```

