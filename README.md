## Create a virtual environment
```
python -m virtualenv ./env
. env/bin/activate
```
Use [flask](https://github.com/pallets/flask)

```
pip install flash
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
