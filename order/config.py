# -*- coding: utf-8 -*-

"""
Definition of a data-taking campaign and the connection of its information to an analysis within a
config.
"""


__all__ = ["Campaign", "Config"]


from .unique import UniqueObject, unique_tree
from .mixins import AuxDataMixin
from .dataset import Dataset
from .util import typed


@unique_tree(cls=Dataset, parents=False)
class Campaign(UniqueObject, AuxDataMixin):
    """ __init__(name, id, ecm=None, bx=None, aux=None, context=None)
    Class that provides data that is subject to a campaign, i.e., a well-defined range of
    data-taking, detector alignment, MC production settings, datasets, etc. Common, generic
    information is available via dedicated attributes, specialized data can be stored as auxiliary
    data.

    *ecm* is the center-of-mass energy, *bx* the bunch-crossing. *aux* is forwarded to the
    :py:class:`AuxDataMixin`, *name*, *id* and *context* to the :py:class:`UniqueObject`
    constructor.

    .. code-block:: python

        c = Campaign("2017B", 1,
            ecm = 13,
            bx  = 25
        )

        d = c.add_dataset("ttH", 1)

        d in c.datasets
        # -> True

        d.campaign == c
        # -> True

    .. py:attribute:: ecm
       type: float

       The center-of-mass energy in arbitrary units.

    .. py:attribute:: bx
       type: float

       The bunch crossing in arbitrary units.
    """

    def __init__(self, name, id, ecm=None, bx=None, aux=None, context=None):
        UniqueObject.__init__(self, name, id, context=context)
        AuxDataMixin.__init__(self, aux=aux)

        # instance members
        self._ecm = None
        self._bx = None

        # set initial values
        if ecm is not None:
            self.ecm = ecm
        if bx is not None:
            self.bx = bx

    @typed
    def ecm(self, ecm):
        # ecm parser
        if not isinstance(ecm, (int, float)):
            raise TypeError("invalid ecm type: %s" % (ecm,))

        return float(ecm)

    @typed
    def bx(self, bx):
        # bx
        if not isinstance(bx, (int, float)):
            raise TypeError("invalid bx type: %s" % (bx,))

        return float(bx)

    def add_dataset(self, *args, **kwargs):
        """
        Adds a child dataset. See :py:meth:`UniqueObjectIndex.add` for more info. Also sets the
        campaign of the added dataset to *this* instance.
        """
        dataset = self.datasets.add(*args, **kwargs)

        # update the dataset campaign
        dataset.campaign = None
        dataset._campaign = self

        return dataset

    def remove_dataset(self, *args, **kwargs):
        """
        Removes a child dataset. See :py:meth:`UniqueObjectIndex.remove` for more info. Also resets
        the campaign of the added dataset.
        """
        dataset = self.datasets.remove(*args, **kwargs)

        # reset the dataset campaign
        if dataset:
            dataset._campaign = None

        return dataset


class Config(AuxDataMixin):
    """
    TODO.
    """
