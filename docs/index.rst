.. Creepo documentation master file, created by
   sphinx-quickstart on Thu Dec 28 06:49:51 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

**Creepo** - a caching, multi-format repository / proxy for small network usage


Once in a while you find yourself on a network put together by unsupervised children.  In such case you may find a spurrious proxy or other blocker which prevents your team from actually producing any code because you can't reach the outside world.

These are the times that you realize that you must be slightly smarter than the machines that you serve.

And always you must have already forgotten more than your network engineer will ever know.

**By default, Creepo doesn't actually cache anything.**  That would be creepy.  And potentially unsafe.

Instead, Creepo is intended to be configured with a global proxy to act as a sort of gateway to various artifact repositories, either inside or outside of the local network.

- Use Creepo behind a corporate firewall to proxy well used upstream repositories, such as npm, pip, maven, composer, apk, and docker.  This allows you to shape network traffic efficiently.

- Use Creepo to take a "snapshot" of build dependencies for later analysis, such as license query or vulnerability scans.

- Use Creepo to facilitate an "air-gapped" installation of some other application.

-- `Visit the repository <https://github.com/dooleydiligent/creepo>`_
| `PyDoc <https://dooleydiligent.github.io/creepo/sphinx/index.html>`_
| `Unit Test Coverage <https://dooleydiligent.github.io/creepo/htmlcov/index.html>`_


==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
