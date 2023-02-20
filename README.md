<center>
  <a href="https://github.com/riga/order">
    <img src="https://media.githubusercontent.com/media/riga/order/master/assets/logo240.png" />
  </a>
</center>


<!-- marker-after-logo -->


[![Documentation status](https://readthedocs.org/projects/python-order/badge/?version=latest)](http://python-order.readthedocs.io/en/latest)
[![Lint and test](https://github.com/riga/order/actions/workflows/lint_and_test.yml/badge.svg)](https://github.com/riga/order/actions/workflows/lint_and_test.yml)
[![Code coverge](https://codecov.io/gh/riga/order/branch/master/graph/badge.svg?token=SNFRGYOITJ)](https://codecov.io/gh/riga/order)
[![Package version](https://img.shields.io/pypi/v/order.svg?style=flat)](https://pypi.python.org/pypi/order)
[![License](https://img.shields.io/github/license/riga/order.svg)](https://github.com/riga/order/blob/master/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/order.svg)](https://pypi.python.org/pypi/order)
[![Open in colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/riga/order/blob/master/examples/intro.ipynb)
[![Open in binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/riga/order/master?filepath=examples%2Fintro.ipynb)

If you're designing a high-energy physics analysis (e.g. with data recorded by an [LHC](https://home.cern/topics/large-hadron-collider) experiment at [CERN](http://home.cern), manual bookkeeping of external data can get complicated quite fast.
*order* provides a pythonic class collection that helps you structuring

- analyses,
- MC campaigns,
- datasets,
- physics process and cross sections,
- channels,
- categories,
- variables, and
- systematic shifts.


<!-- marker-after-header -->


## Getting started

See the [intro.ipynb](https://github.com/riga/order/blob/master/examples/intro.ipynb) notebook for an introduction to the most important classes and an example setup of a small analysis.
You can also run the notebook interactively on colab or binder:

[![Open in colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/riga/order/blob/master/examples/intro.ipynb)
[![Open in binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/riga/order/master?filepath=examples%2Fintro.ipynb)

You can find the full [API documentation on readthedocs](http://python-order.readthedocs.io).


<!-- marker-after-getting-started -->


## Projects using order

- [uhh-cms/cmsdb](https://github.com/uhh-cms/cmsdb)
- tba


## Installation and dependencies

Install *order* via [pip](https://pypi.python.org/pypi/order):

```shell
pip install order
```

The only dependencies are [scinum](https://pypi.python.org/pypi/scinum) and [six](https://pypi.python.org/pypi/six) (Python 2 support that will be dropped soon), which are installed with the above command.


## Contributing and testing

If you like to contribute, feel free to open a pull request 🎉.
Just make sure to add new test cases and run them via:

```shell
python -m unittest tests
```

In general, tests should be run for Python 2.7, 3.6 - 3.11.
To run tests in a docker container, do

```shell
# run the tests
./tests/docker.sh python:3.9

# or interactively by adding a flag "1" to the command
./tests/docker.sh python:3.9 1
> pip install -r requirements.txt
> python -m unittest tests
```

In addition, [PEP 8](https://www.python.org/dev/peps/pep-0008) compatibility should be checked with [flake8](https://pypi.org/project/flake8):

```shell
flake8 order tests setup.py
```


## Development

- Source hosted at [GitHub](https://github.com/riga/order)
- Report issues, questions, feature requests on [GitHub Issues](https://github.com/riga/order/issues)
