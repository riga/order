# coding: utf-8

"""
Definition of the central analysis class.
"""


__all__ = ["Analysis"]


from order.unique import UniqueObject, unique_tree
from order.mixins import AuxDataMixin
from order.config import Config


@unique_tree(cls=Config, parents=False)
class Analysis(UniqueObject, AuxDataMixin):
    """ __init__(name, id, configs=None, aux=None, context=None)
    The analysis class which represents the central object of a physics analysis. Yet, it is quite
    lightweight as most information is contained in :py:class:`~order.config.Config` objects in the
    scope of a :py:class:`~order.config.Campaign`. In addition, it provides some convenience methods
    to directly access objects in deeper data structures.

    **Arguments**

    The configuration objects are initialized with *configs*. *aux* is forwarded to the
    :py:class:`~order.mixins.AuxDataMixin`, *name*, *id* and *context* to the
    :py:class:`~order.unique.UniqueObject` constructor.

    **Example**

    For usage examples, see the
    `examples directory <https://github.com/riga/order/tree/master/examples>`_.

    **Members**
    """

    def __init__(self, name, id, configs=None, aux=None, context=None):
        UniqueObject.__init__(self, name, id, context=context)
        AuxDataMixin.__init__(self, aux=aux)

        # set initial configs
        if configs is not None:
            self.configs.extend(configs)

    def get_channels(self, config):
        """
        Returns the :py:class:`~order.unique.UniqueObjectIndex` of channels that belong to a
        *config* that was previously added. Shorthand for ``get_config(config).channels``.
        """
        return self.get_config(config).channels

    def get_categories(self, config):
        """
        Returns the :py:class:`~order.unique.UniqueObjectIndex` of categories that belong to a
        *config* that was previously added. Shorthand for ``get_config(config).categories``.
        """
        return self.get_config(config).categories

    def get_datasets(self, config):
        """
        Returns the :py:class:`~order.unique.UniqueObjectIndex` of datasets that belong to a
        *config* that was previously added. Shorthand for ``get_config(config).datasets``.
        """
        return self.get_config(config).datasets

    def get_processes(self, config):
        """
        Returns the :py:class:`~order.unique.UniqueObjectIndex` of processes that belong to a
        *config* that was previously added. Shorthand for ``get_config(config).processes``.
        """
        return self.get_config(config).processes

    def get_variables(self, config):
        """
        Returns the :py:class:`~order.unique.UniqueObjectIndex` of variables that belong to a
        *config* that was previously added. Shorthand for ``get_config(config).variables``.
        """
        return self.get_config(config).variables

    def get_shifts(self, config):
        """
        Returns the :py:class:`~order.unique.UniqueObjectIndex` of shifts that belong to a *config*
        that was previously added. Shorthand for ``get_config(config).shifts``.
        """
        return self.get_config(config).shifts

    def add_config(self, *args, **kwargs):
        """
        Adds a child config. See :py:meth:`order.unique.UniqueObjectIndex.add` for more info. Also
        sets the analysis of the added config to *this* instance. Returns the added config object.
        """
        config = self.configs.add(*args, **kwargs)

        # update the config's analysis
        config.analysis = None
        config._analysis = self

        return config

    def remove_config(self, *args, **kwargs):
        """
        Removes a child config. See :py:meth:`order.unique.UniqueObjectIndex.remove` for more info.
        Also resets the analysis of the added config. Returns the removed config object.
        """
        config = self.configs.remove(*args, **kwargs)

        # reset the config's analysis
        if config:
            config._analysis = None

        return config
