from bottle import Bottle, route, run
app = Bottle()
print('registering /blog')

@app.route("/")
def index():
    """Show all the posts, most recent first."""
    print('processing /')
    return('blog')
