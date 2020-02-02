import logging

class Logger(object):
  def __init__(self, name):
    # create logger
    logger = logging.getLogger(name)
    self._name = name
    #
    self._logger = logger
    # key = 'LOGGING_{name}'.format(name=__name__).replace('.', '_')
    loglevel = logging.DEBUG
    # if key is not None:
    #   if os.environ[key]:
    #     loglevel = os.environ[key]

    logger.setLevel(loglevel)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    #

  def info(self, message):
    self._logger.info('{message}'.format(message=message))
  def debug(self, message):
    self._logger.debug('{message}'.format(message=message))
  def warn(self, message):
    self._logger.warn('{message}'.format(message=message))
