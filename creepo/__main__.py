"""The server part of creepo"""
import logging
import os
from pathlib import Path
import ssl
import threading
import yaml

import cherrypy

from composerproxy import ComposerProxy
from pipproxy import PipProxy
from npmproxy import NpmProxy
from simpleproxy import SimpleProxy

# this file's parent directory
PROJECT_DIR = Path(Path(__file__).parent.resolve().absolute()
                   ).parent.resolve().absolute()

if __name__ == '__main__':

    logger = cherrypy.log.error_log

    config = {}
    if os.path.exists('config.yml'):
        with open(f"{PROJECT_DIR}/config.yml", encoding="utf-8") as file:
            config = yaml.safe_load(file.read())
    else:
        logger.info('No config found - all defaults accepted')
    if config.get('log_level') is None:
        config['log_level'] = logging.INFO

    logging.getLogger().setLevel(config['log_level'])
    logger.setLevel(config['log_level'])
    logger.propagate = True
    logger.info('log_level set to %s', config['log_level'])
    config['logger'] = logger

    if 'port' not in config:
        config['port'] = 4443

    if 'server' not in config:
        config['server'] = 'localhost'

    if 'proxy' in config:
        logger.info('Using global proxy at %s', config['proxy'])

    cert = f"{PROJECT_DIR}/server.pem"
    key = f"{PROJECT_DIR}/server.key"
    client = f"{PROJECT_DIR}/client.pem"

    logger.info('Configuring SSL version %s', ssl.OPENSSL_VERSION)
    with open(client, 'r', encoding='utf-8') as f:
        output = f.read()
        f.close()
        logger.info(
            'Use the following certificate to secure your client(s)\n\n%s\n\n', output)
    
    thread_pool = 10
    if 'thread_pool' in config:
        thread_pool = config['thread_pool']
    logger.info(f'Setting thread pool to {thread_pool}')

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': config['port'],
        'server.ssl_module': 'builtin',
        'server.ssl_certificate': cert,
        'server.ssl_private_key': key,
        'server.ssl_certificate_chain': client,
        'server.thread_pool': thread_pool
    })

    # logger.debug('instantiating mavenProxy at /m2')
    # cherrypy.tree.graft(MavenProxy(config).proxy, '/m2')

    logger.debug('instantiating proxy at /npm')
    cherrypy.tree.graft(NpmProxy(config).proxy, '/npm')

    logger.debug('instantiating pipproxy at /pip')
    cherrypy.tree.graft(PipProxy(config).proxy, '/pip')

    # logger.debug('instantiating dockerproxy at /v2')
    # cherrypy.tree.graft(GenericProxy(config).proxy, '/v2')

    logger.debug('instantiating composerproxy at /composer')
    cherrypy.tree.graft(ComposerProxy(config).proxy, '/p2')

    # logger.debug('instantiating apkproxy at /alpine')
    # cherrypy.tree.graft(ApkProxy(config).proxy, '/alpine')

    for k in config['dynamic']:
        config[k] = config['dynamic'][k]
        cherrypy.tree.graft(SimpleProxy(config, k).proxy, f"/{k}")

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
