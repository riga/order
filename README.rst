.. figure:: https://raw.githubusercontent.com/riga/order/master/logo240.png
   :target: https://github.com/riga/order
   :align: center
   :alt: order logo


.. marker-after-logo


.. image:: https://github.com/riga/order/actions/workflows/lint_and_test.yml/badge.svg
   :target: https://github.com/riga/order/actions/workflows/lint_and_test.yml
   :alt: Lint and test

.. image:: https://readthedocs.org/projects/python-order/badge/?version=latest
   :target: http://python-order.readthedocs.io/en/latest
   :alt: Documentation status

.. image:: https://img.shields.io/pypi/v/order.svg?style=flat
   :target: https://pypi.python.org/pypi/order
   :alt: Package version

.. image:: https://img.shields.io/github/license/riga/order.svg
   :target: https://github.com/riga/order/blob/master/LICENSE
   :alt: License

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/riga/order/master?filepath=examples%2Fintro.ipynb
   :alt: Open in binder


If you're designing a high-energy physics analysis (e.g. with data recorded by an `LHC <https://home.cern/topics/large-hadron-collider>`__ experiment at `CERN <http://home.cern>`__), manual bookkeeping of external data can get complicated quite fast. *order* provides a pythonic class collection that helps you structuring

- analyses,
- MC campaigns,
- datasets,
- physics process and cross sections,
- channels,
- categories,
- variables, and
- systematic shifts.


.. marker-after-header


Getting started
---------------

See the `intro.ipynb <https://github.com/riga/order/blob/master/examples/intro.ipynb>`__ notebook for an introduction to the most important classes and an example setup of a small analysis. You can also run the notebook interactively on binder:

|binder|

You can find the full `API documentation on readthedocs <http://python-order.readthedocs.io>`__.


.. marker-after-getting-started


Installation and dependencies
-----------------------------

Install *order* via `pip <https://pypi.python.org/pypi/order>`__:

.. code-block:: shell

   pip install order

The only dependencies are `scinum <https://pypi.python.org/pypi/scinum>`__ and `six <https://pypi.python.org/pypi/six>`__, which are installed with the above command.


Contributing and testing
------------------------

If you like to contribute, I'm happy to receive pull requests. Just make sure to add new test cases and run them via:

.. code-block:: shell

   python -m unittest tests

In general, tests should be run for Python 2.7, 3.6, 3.7 and 3.8. To run tests in a docker container, do

.. code-block:: shell

   # run the tests
   ./tests/docker.sh python:3.8

   # or interactively by adding a flag "1" to the command
   ./tests/docker.sh python:3.8 1
   > pip install -r requirements.txt
   > python -m unittest tests

In addition, `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`__ compatibility should be checked with `flake8 <https://pypi.org/project/flake8/>`__:

.. code-block:: shell

   flake8 order tests setup.py


Development
-----------

- Source hosted at `GitHub <https://github.com/riga/order>`__
- Report issues, questions, feature requests on `GitHub Issues <https://github.com/riga/order/issues>`__


.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/riga/order/master?filepath=examples%2Fintro.ipynb
   :alt: Open in binder
