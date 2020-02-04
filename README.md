## Create a virtual environment
```
python3 -m venv venv
. venv/bin/activate
```
Install [creepo](https://github.com/dooleydiligent/creepo)

```
pip install -e .
```

# Run it
```
export BOTTLE_APP=creepo
export BOTTLE_ENV=development
#$ flask init-db
# flask run
python creepo
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
