
import cherrypy
import creepo
import mavenproxy
import os
from pathlib import Path
import ssl
# this file's parent directory
PROJECT_DIR = Path(Path(__file__).parent.resolve().absolute()
                   ).parent.resolve().absolute()

if __name__ == '__main__':
    cert = '{dir}/server.pem'.format(dir=PROJECT_DIR)
    key = '{dir}/server.key'.format(dir=PROJECT_DIR)
    
    print('SSL version {ssl}'.format(ssl=ssl.OPENSSL_VERSION))
    cherrypy.log(
        'instantiating mavenProxy at /m2 with server {cert} and {key}'.format(cert=cert, key=key))
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 4443,
        'server.ssl_module': 'pyopenssl',
        'server.ssl_certificate': cert,
        'server.ssl_private_key': key,
    })
    cherrypy.tree.graft(mavenproxy.MavenProxy().m2, '/m2')
    cherrypy.tree.mount(None, '/',
                        {
                            '/favicon.ico':
                            {
                                'tools.staticfile.on': True,
                                'tools.staticdir.root': os.getcwd(),
                                'tools.staticfile.filename': './creepo/favicon.ico'
                            },
                            '/coverage':
                            {
                                'tools.staticdir.on': True,
                                'tools.staticdir.root': os.getcwd(),
                                'tools.staticdir.dir': './htmlcov'
                            },
                        })
    # cherrypy.tree.mount(creepo.Creepo(), '/', base)
    # m2_dispatcher = cherrypy.dispatch.RoutesDispatcher()
    # m2_dispatcher.connect('mavenproxy', '', mavenproxy.MavenProxy().m2)

    # m2_config = {
    #     '/':
    #     {
    #         'request.dispatch': m2_dispatcher,
    #     },
    # }

    # cherrypy.tree.mount(mavenproxy.MavenProxy(), '/m2', m2_config)
    # cherrypy.log('mounted mavenProxy at /m2')

    # import npmproxy
    # import pipproxy
    # import blog, mavenproxy, npmproxy, pipproxy, proxy
    # app.mount('/blog', blog.app)
    # app.mount('/proxy', proxy.app)
    cherrypy.log('starting the engine')
    cherrypy.engine.start()
    cherrypy.engine.block()
    cherrypy.log('engine stopped')
