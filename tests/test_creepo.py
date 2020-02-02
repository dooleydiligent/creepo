from webtest import TestApp
from creepo import app

# def test_config():
#   """Test create_app without passing test config."""
# #    assert not creepo.create_app().testing
#   print('creepo is {creepo}'.format(creepo=creepo))
#   assert creepo.create_app({"TESTING": True})


def test_hello():
  myapp = TestApp(app)
  response = myapp.get('/hello')
  assert response.body == b"Hello, World!"
