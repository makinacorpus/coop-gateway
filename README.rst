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

Testing
=======

Create a django-coop project.

Install coop-gateway in develop mode.

Configure coop-gateway.

Install and configure `django-nose`_.

Run tests::

    cd project
    python manage.py test coop_gateway

.. _`django-nose`: https://pypi.python.org/pypi/django-nose

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
