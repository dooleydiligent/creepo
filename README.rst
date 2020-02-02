# Creepo
  - a cachining multi-format repository proxy for small network usage

# Motivation
Once in a while you find yourself on a network put together by unsupervised children.  In such case
you may find a spurrious proxy or network other blocker which prevents your team from actually producing any code.

These are the times that you realize that you must be slightly smarter than the machines that you use.

And always you must have already forgottem more than your network engineer will ever know.

Use Creepo to cache well used upstream repositories, such as npm, pip, and maven.  More will follow shortly.

# Install

### clone the repository
```
git clone git@github.com:dooleydiligent/creepo.git
cd creepo
```

# Create a virtualenv and activate it
- Just do it with python 3.  Eventually you don't notice the pain
```
python3 -m venv venv
. venv/bin/activate
```
# Install Creepo
```
pip install -e .
```

# Run
```
export BOTTLE_APP=creepo
export BOTTLE_ENV=development

python creepo >creepo.log 2>&1
```

# Test
```
pip3 install '.[test]'
pytest
```

# Run with coverage report
```
coverage run -m pytest
coverage report
coverage html  # open htmlcov/index.html in a browser
```

# Use it as a Maven proxy repo
```
mvn dependency:get \
    -DrepoUrl=http://localhost:5000/m2/ \
    -Dartifact=org.sonatype.nexus.plugins:nexus-plugins:3.19.0-01 \
    -s ./mvn/settings.xml
```

# Use it as an npm proxy repo
```
cd client
npm install --registry=http://localhost:5000/npm/
```

# Use it as a pip proxy repo
```
pip install -e . -i http://localhost:5000/pip/
```
