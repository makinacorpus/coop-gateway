Coop-Gateway
============

Coop-Gateway is an application to interface two Django-Coop instances.

Installation
============

Setup
-----

For production::

    python setup.py install


For development::

    python setup.py develop

Configure
---------

Add 'coop_gateway' to the INSTALLED_APPS.

Add the url of the aggregator to your settings::

    PES_HOST = 'http://domain.tld'

Add the API key of the aggregator to your settings::

    PES_API_KEY = 'TheApiKey'

Create the required tables with::

    python manage.py syncdb

Enable retrieving from PES_HOST add a cron job with::

    python manage.py pes_import

Credits
=======

Companies
---------

|MakinaCorpusLogo|_

  * `Makina Corpus <http://www.makina-corpus.com>`_
  * `Contact us <mailto:python@makina-corpus.org>`_

.. |MakinaCorpusLogo| image:: http://depot.makina-corpus.org/public/logo.gif
.. _`MakinaCorpusLogo`:  http://www.makina-corpus.com

Authors
-------

  * Antoine Cezar

License
=======

Coop-Gateway use the BSD (2-clause) License.
See the LICENSE file for more informations.
