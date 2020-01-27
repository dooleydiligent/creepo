## Create a virtual environment
```
cd server
python -m virtualenv ./env
. env/bin/activate
```
Use [flask](https://github.com/pallets/flask)

```
pip install -r requirements.txt
```

Code quality [demo](https://github.com/pallets/flask/tree/master/examples/tutorial)

## Test
```
pip install '.[test]'
```

## Run with coverage
```
coverage run -m pytest
coverage report
coverage html  # open htmlcov/index.html in a browser
```

## Code quality
```
pip install pylint-json2html
pip install pylint
pylint creepo | pylint-json2html -o creepo-lint.html
```
# Run it
```
python .
```

# Maven proxy repo
```
mvn dependency:get \
    -DrepoUrl=http://localhost:5000/m2/ \
    -Dartifact=org.sonatype.nexus.plugins:nexus-plugins:3.19.0-01 \
    -s ./mvn/settings.xml
```

# npm proxy repo
```
cd client
npm install --registry=http://localhost:5000/npm/
```

# pip proxy repo
```
cd server
pip install -r requirements.txt -i http://localhost:5000/pip/
```
