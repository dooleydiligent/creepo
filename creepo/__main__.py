"""The server part of creepo"""
import logging
import os
from pathlib import Path
import ssl
import yaml

import cherrypy

from dockerproxy import DockerProxy
from composerproxy import ComposerProxy
from mvnproxy import MavenProxy
from pipproxy import PipProxy
from npmproxy import NpmProxy

# this file's parent directory
PROJECT_DIR = Path(Path(__file__).parent.resolve().absolute()
                   ).parent.resolve().absolute()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    logger = cherrypy.log.error_log
    logger.setLevel(logging.DEBUG)
    logger.propagate = True

    config = {}
    if os.path.exists('config.yml'):
        logger.info('Configuring from file')
        with open(f"{PROJECT_DIR}/config.yml", encoding="utf-8") as file:
            config = yaml.safe_load(file.read())
    else:
        logger.info('No config found')
    if 'port' not in config:
        config['port'] = 4443

    if 'proxy' in config:
        logger.info('Using global proxy at %s', config['proxy'])

    cert = f"{PROJECT_DIR}/server.pem"
    key = f"{PROJECT_DIR}/server.key"
    client = f"{PROJECT_DIR}/client.pem"

    logger.info('Configuring SSL version %s', ssl.OPENSSL_VERSION)
    with open(client, 'r', encoding='utf-8') as f:
        output = f.read()
        f.close()
        logger.info('Use the following certificate to secure your client(s)\n\n%s\n\n', output)

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': config['port'],
        'server.ssl_module': 'pyopenssl',
        'server.ssl_certificate': cert,
        'server.ssl_private_key': key,
        'server.ssl_certificate_chain': client,
    })

    logger.debug('instantiating mavenProxy at /m2')
    cherrypy.tree.graft(MavenProxy(config, logger).m2, '/m2')

    logger.debug('instantiating proxy at /npm')
    cherrypy.tree.graft(NpmProxy(config, logger).npm, '/npm')

    logger.debug('instantiating pipproxy at /pip')
    cherrypy.tree.graft(PipProxy(config, logger).pip, '/pip')

    logger.debug('instantiating dockerproxy at /v2')
    cherrypy.tree.graft(DockerProxy(config, logger).v2, '/v2')

    logger.debug('instantiating composerproxy at /composer')
    cherrypy.tree.graft(ComposerProxy(config, logger).p2, '/p2')

    cherrypy.tree.mount(None, '/',
                        {
                            '/favicon.ico':
                            {
                                'tools.staticfile.on': True,
                                'tools.staticdir.root': os.getcwd(),
                                'tools.staticfile.filename': f"{PROJECT_DIR}/creepo/favicon.ico"
                            },
                            '/coverage':
                            {
                                'tools.staticdir.on': True,
                                'tools.staticdir.root': os.getcwd(),
                                'tools.staticdir.dir': './htmlcov'
                            },
                        })

    logger.info('\n\nStarting the engine with config %s', config)
    cherrypy.engine.start()
    cherrypy.engine.block()
    logger.info('Engine stopped')
