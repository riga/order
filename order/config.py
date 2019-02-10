# coding: utf-8

"""
Definition of a data-taking campaign and the connection of its information to an analysis within a
config.
"""


__all__ = ["Campaign", "Config"]


from order.unique import UniqueObject, unique_tree
from order.mixins import CopyMixin, AuxDataMixin
from order.shift import Shift
from order.dataset import Dataset
from order.process import Process
from order.category import Channel, Category
from order.variable import Variable
from order.util import typed


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

    def __init__(self, name, id, ecm=None, bx=None, datasets=None, aux=None, context=None):
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

        if datasets is not None:
            self.datasets.extend(datasets)

    @typed
    def ecm(self, ecm):
        # ecm parser
        if not isinstance(ecm, (int, float)):
            raise TypeError("invalid ecm type: {}".format(ecm))

        return float(ecm)

    @typed
    def bx(self, bx):
        # bx parser
        if not isinstance(bx, (int, float)):
            raise TypeError("invalid bx type: {}".format(bx))

        return float(bx)

    def add_dataset(self, *args, **kwargs):
        """
        Adds a child dataset and returns it. See :py:meth:`UniqueObjectIndex.add` for more info.
        Also sets the campaign of the added dataset to *this* instance.
        """
        dataset = self.datasets.add(*args, **kwargs)

        # update the dataset's campaign
        dataset.campaign = None
        dataset._campaign = self

        return dataset

    def remove_dataset(self, *args, **kwargs):
        """
        Removes a child dataset. See :py:meth:`UniqueObjectIndex.remove` for more info. Also resets
        the campaign of the added dataset.
        """
        dataset = self.datasets.remove(*args, **kwargs)

        # reset the dataset's campaign
        if dataset:
            dataset._campaign = None

        return dataset


@unique_tree(cls=Dataset, parents=False)
@unique_tree(cls=Process, plural="processes", parents=False, deep_children=True)
@unique_tree(cls=Channel, parents=False, deep_children=True)
@unique_tree(cls=Category, plural="categories", parents=False, deep_children=True)
@unique_tree(cls=Variable, parents=False)
@unique_tree(cls=Shift, parents=False)
class Config(UniqueObject, CopyMixin, AuxDataMixin):
    """ __init__(campaign, name=None, id=None, analysis=None, datasets=None, processes=None, channels=None, categories=None, variables=None, shifts=None, aux=None, context=None)
    Class holding analysis information that is related to a :py:class:`Campaign` instance. Most of
    the analysis configuration happens here.

    It stores analysis *datasets*, *processes*, *channels*, *categories*, *variables*, and *shifts*
    which are initialized from constructor arguments, as well as references to the
    :py:class:`Analysis` and :py:class:`Campaign` instances it belongs to. *name*, *id* and
    *context* are forwarded to the :py:class:`UniqueObject` constructor. *name* and *id* default to
    the values of the *campaign* instance. Specialized data such as integrated luminosities,
    triggers, or statistical models can be stored as auxiliary data.

    .. code-block:: python

        analysis = Analysis("ttH", 1, ...)
        campaign = Campaign("2017B", 1, ...)

        c = analysis.add_config(campaign)

        c.name, c.id
        # -> "2017B", 1

        # start configuration
        c.add_dataset(campaign.get_dataset("ttH_bb"))
        c.add_process("ttH_bb", 1, xsecs={13: 0.5071})
        bb = c.add_channel("bb", 1)
        bb.add_category("eq6j_eq4b")
        c.add_variable("jet1_px", expression="jet1_pt * cos(jet1_phi)")
        c.add_shift("pdf_up", type=Shift.SHAPE)
        ...

        # at some point you might want to create a second config
        # with other values for that campaign, e.g. for sub-measurements
        c2 = analysis.add_config(campaign, name="sf_meausurement", id=2)
        ...

    .. py:attribute:: campaign
       type: Campaign
       read-only

       The :py:class:`Campaign` instance this config belongs to.

    .. py:attribute:: analysis
       type: Analysis
       read-only

       The :py:class:`Analysis` instance this config belongs to. When set, *this* config is added
       to the index of configs of the analysis object.
    """

    copy_builtin = False
    copy_attrs = ["datasets", "processes", "channels", "categories", "variables", "shifts", "aux",
                  "context"]
    copy_ref_attrs = ["campaign", "analysis"]

    def __init__(self, campaign=None, name=None, id=None, analysis=None, datasets=None,
            processes=None, channels=None, categories=None, variables=None, shifts=None, aux=None,
            context=None):
        # instance members
        self._campaign = None
        self._analysis = None

        # if name or id are None, campaign must be set
        # use the campaign setter for type validation first
        self.campaign = campaign
        if name is None:
            if self.campaign is None:
                raise ValueError("a name must be set when campaign is missing")
            name = self.campaign.name
        if id is None:
            if self.campaign is None:
                raise ValueError("an id must be set when campaign is missing")
            id = self.campaign.id

        UniqueObject.__init__(self, name=name, id=id, context=context)
        AuxDataMixin.__init__(self, aux=aux)

        # set initial values
        if analysis is not None:
            self.analysis = analysis

        if datasets is not None:
            self.datasets.extend(datasets)

        if processes is not None:
            self.processes.extend(processes)

        if channels is not None:
            self.channels.extend(channels)

        if categories is not None:
            self.categories.extend(categories)

        if variables is not None:
            self.variables.extend(variables)

        if shifts is not None:
            self.shifts.extend(shifts)

    @typed
    def campaign(self, campaign):
        # campaign parser
        if not isinstance(campaign, Campaign) and campaign is not None:
            raise TypeError("invalid campaign type: {}".format(campaign))

        return campaign

    @property
    def analysis(self):
        # analysis getter
        return self._analysis

    @analysis.setter
    def analysis(self, analysis):
        # analysis setter
        if analysis is not None and not isinstance(analysis, Analysis):
            raise TypeError("invalid analysis type: {}".format(analysis))

        # remove this config from the current analysis' config index
        if self._analysis:
            self._analysis.configs.remove(self)

        # add this config to the analysis' config index
        if analysis:
            analysis.configs.add(self)

        self._analysis = analysis


# prevent circular imports
from .analysis import Analysis
