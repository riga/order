Quickstart
==========

The sections below explain the most important classes, the concept of mixins and some notes on copying objects. Open the `intro.ipynb <https://github.com/riga/order/blob/master/examples/intro.ipynb>`__ notebook to see these classes in action or run it interactively on binder:

|binder|

*order* follows a very strict API design and naming scheme.

1. Methods start with (or at least contain) verbs. E.g. setters and getters are prefixed with ``set_`` and ``get_``, respectively.
2. Properties implement type checks and, where applicable, conversions! Assigments such as ``my_object.some_string_attribute = 123`` (can) immediately fail. This way, type ambiguities during analysis execution are mitigated.
3. The code style is `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`__ compatible (checked via `flake8 <https://pypi.org/project/flake8/>`__).

.. contents:: Contents
   :local:


*UniqueObject* and *UniqueObjectIndex*
--------------------------------------

Before diving into the actual physics-related classes, it is necessary to understand their primary uncerlying base class: :py:class:`~order.unique.UniqueObject`.

A :py:class:`~order.unique.UniqueObject` essentially has three attributes: a *name* (string), an *id* (integer) and a uniqueness *context*. The combination (*name*, *context*) as well as (*id*, *context*) are forced to be unique per inheriting class (see example below). This way, *name* and *id* are logically connected and once used, they cannot be associated to any other object. The mechanism unambiguously assigns

1. a human-readable name to objects (e.g.) for expressive use on the command-line, and
2. a unique identifier to objects (e.g.) for encoding information in data structures such as ROOT trees.

Consider this example implementation of a physics process:

.. code-block:: python

   import order as od

   class Process(od.UniqueObject):

       def __init__(self, name, id, xsec, context=None):
           super(Process, self).__init__(name, id, context=context)

           self.xsec = xsec

When creating a process via

.. code-block:: python

   ttbar = Process("ttbar", 1, 831.76)

   print(ttbar)
   # -> "Process(name=ttbar, id=1, context=process)"

both the *name* ``"ttbar"`` and the *id* ``1`` are globally reserved and no other instance of the same class can be created with that *name* or *id* within the same *context*. For the ``ttbar`` process object that we just created, the *context* argument was *None*, which tells *order* to use a default value (the lower-case class name ``"process"`` in this case). When trying to create another process with e.g. the same id,

.. code-block:: python

   ttbarH = Process("ttbarH", 1, 0.508)
   # -> order.unique.DuplicateIdException: an object with id '1' already exists in the uniqueness context 'process'

an exception (:py:class:`~order.unique.DuplicateIdException`) is raised (or a :py:class:`~order.unique.DuplicateNameException` in case of duplicate names). When the object is placed into an other uniqueness context, however, the instance creation succeeds. This can be achieved by passing a different *context* to the ``Process`` constructor, or via using the :py:meth:`~order.unique.uniqueness_context` guard

.. code-block:: python

   with od.uniqueness_context("other_analysis"):
       ttbarH = Process("ttbarH", 1, 0.508)

   # same as
   # ttbarH = Process("ttbarH", 1, 0.508, context="other_analysis")

   print(ttbarH)
   # -> "Process(name=ttbarH, id=1, context=other_analysis)"

The class itself can be seen as part of the uniqueness context. For other classes that inherit from :py:class:`~order.unique.UniqueObject`, the same (*name*, *context*) and (*id*, *context*) combinations can be used again.

Internally, each class maintains its own instance cache to check for duplicate names and ids. The cache functionality is implemented in :py:class:`~order.unique.UniqueObjectIndex`. Additionaly, this class is (mainly) employed for constructing **has** / **owns** relations between objects. Let's extend the example above by creating a simple *Dataset* class that is aware of the physics processes it contains:

.. code-block:: python

   class Dataset(od.UniqueObject):

       def __init__(self, *args, **kwargs):
           super(Dataset, self).__init__(*args, **kwargs)

           self.processes = UniqueObjectIndex(cls=Process)

   dataset_ttbar = Dataset("ttbar", 1)
   dataset_ttbar.processes.add(ttbar)

   print(dataset_ttbar.processes)
   # -> "UniqueObjectIndex(cls=Process, len=1)"

You will find similar constructs all across *order*, however, with several convenience methods.
To reflect the uniqueness rules explained above, a :py:class:`~order.unique.UniqueObjectIndex` stores objects per *context*. When studying the API reference, you will notice a *context* argument in the signatures of most of its methods (such as :py:meth:`~order.unique.UniqueObjectIndex.len`, :py:meth:`~order.unique.UniqueObjectIndex.names`, :py:meth:`~order.unique.UniqueObjectIndex.ids`, :py:meth:`~order.unique.UniqueObjectIndex.keys` or :py:meth:`~order.unique.UniqueObjectIndex.values`). For instance, ``processes.len()`` will return 1, whereas ``processes.len(context="other_analysis")`` will return 0 as no object with the uniquess context ``"other_analysis"`` was added yet.


*Analysis*, *Campaign* and *Config*
-----------------------------------

An instance of the :py:class:`~order.analysis.Analysis` class represents the overarching object containing information of a physics analysis.

Varying requirements across data-taking periods, complex sub measurements, or simply different revisions of the same analysis are typical reasons why the structuring of information is quite demanding over the course of an analysis with sometimes unpredictable incidents and deadlines (code ↔︎ time uncertainty is a thing). For this purpose, *order* introduces two classes: :py:class:`~order.config.Campaign` and :py:class:`~order.config.Config`.

A :py:class:`~order.config.Campaign` describes and contains **analysis-independent** information, such as detector alignment settings, event simulation settings, recorded / simulated datasets, etc. In general, a pre-configured campaign object could be provided centrally by a working group or collaboration.

A :py:class:`~order.config.Config` object holds **analysis-dependent** information related to a certain campaign. Thus, a config is unambiguously assigned to both an analysis and a campaign.

Consider, for example, offline triggers that are used to select events specifically in one analysis. By construction, they should not be stored in a campaign object (which is **analysis-independent**), but they might also change between different data-taking periods and therefore should not be stored in the analysis object itself. Instead, a config object is an ideal place for such information.

.. code-block:: python

   import order as od

   # the campaign (could be configured externally)
   campaign_2018 = od.Campaign("data_taking_2018", 1, ecm=13)

   # create the analysis
   analysis = od.Analysis("my_analysis", 1)

   # add a config for the 2018 campaign
   # when no name or id are passed, it has the same as the campaign
   cfg = analysis.add_config(campaign_2018)

   # add trigger information as auxiliary data
   cfg.set_aux("triggers", ["trigger_ee", "trigger_emu", "trigger_mumu"])

An analysis can contain several config objects for the same campaign. Just note that uniqueness rules apply here as well.

See the `intro.ipynb <https://github.com/riga/order/blob/master/examples/intro.ipynb>`__ notebook for more examples.


*Dataset* and *Process*
-----------------------

Physics processes and simualted / recorded datasets are described by two classes: :py:class:`~order.process.Process` and :py:class:`~order.dataset.Dataset`.

Besides a *name* and an *id*, a :py:class:`~order.process.Process` object has cross sections for different center-of-mass energies, labels and colors for plotting purposes, and information about whether or not it describes real data or MC (it inherits from the :py:class:`~order.mixins.DataSourceMixin`, see `mixin classes <mixin-classes>`__). Cross section values are automatically converted to `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instances, which are able to store multiple uncertainties, provide automatic error propagation and also support NumPy arrays.

Moreover, processes can have subprocesses and *order* provides convenience methods to work with arbitrarily deep process lookup.

.. code-block:: python

   import order as od
   from scinum import Number, UP, DOWN, REL, ABS

   ttH = od.Process("ttH", 1,
       xsecs={
           13: Number(0.5071, {
               "scale": (REL, 0.058, 0.092),  # relative scale uncertainty of +5.8/-9.2 %
               "pdf"  : (REL, 0.036),         # relative pdf uncertainty of +-3.6 %
           }),
       },
      label=r"t\bar{t}H",
      color=(255, 0, 0),
   )

   # print the ttH cross section at 13 TeV with the up-shifted scale uncertainty
   print(ttH.get_xsec(13)(UP, "scale"))
   # -> 0.5365118

   print(ttH.get_xsec(13).__class__)
   # -> "scinum.Number"

   # add the ttH (H -> bb) subprocess
   ttH_bb = ttH.add_process("ttH_bb", 2,
       xsecs={
           13: ttH.get_xsec(13) * 0.5824,  # branching ratio of H -> bb
       },
       label=ttH.label + r", H \rightarrow b\bar{b}",
   )

   # again, print the cross section for the up-shfited uncertainty, note the correct propagation
   print(ttH_bb.get_xsec(13)(UP, "scale"))
   # -> 0.3124645

   # print the label in ROOT-style latex
   print(ttH_bb.label_root)
   # -> "t#bar{t}H, H #rightarrow b#bar{b}"

   # check that the subprocess is really contained in the ttH subprocesses
   print("ttH_bb" in ttH.processes)
   # -> True

Information about datasets is stored in :py:class:`~order.dataset.Dataset` objects. Standard attributes are *name* and *id*, labels, and data/MC information. Optionally, a dataset can be assigned to a :py:class:`~order.config.Campaign` and to one or more :py:class:`~order.process.Process` objects. Let's extend the above example:

.. code-block:: python

   dataset_ttH_bb = od.Dataset("ttH_bb", 1,
       campaign=campaign_2018,
       processes=[ttH_bb],
       n_files=1000,
   )

   # the campaign is now aware of this dataset
   print(dataset_ttH_bb in campaign_2018.datasets)
   # -> True

   # and the dataset knows about the ttH_bb process
   print(ttH_bb in dataset_ttH_bb.processes)
   # -> True

   # as a little exercise, get all ttH subprocesses which are contained in the dataset
   # this is, of course, only the ttH_bb process itself
   print([p for p in ttH.processes if p in dataset_ttH_bb.processes])
   # -> ["<Dataset at 0x1169421d0, name=ttH_bb, id=1, context=dataset>"]

   # print the number of files
   print(datasaet_ttH_bb.n_files)
   # -> 1000

The last statement prints the number of files in that dataset. But what happens when systematic variations exist for that dataset? Let's assume there are two variants that were generated with different top quark masses. Do we create two additional datasets? **No**. They are stored in the same dataset object.

A dataset stores :py:class:`~order.dataset.DatasetInfo` objects, containing information that may vary (e.g.) across systematic uncertainties. Examples are the number of files, the number of total events, or arbitrary auxiliary information (see the :py:class:`~order.mixins.AuxDataMixin` in the `mixin classes <mixin-classes>`__ below). In fact, the number of files ``n_files`` above is already stored in a :py:class:`~order.dataset.DatasetInfo` object, stored as ``dataset_ttH_bb.info["nominal"]``. The attributes ``n_files`` and ``n_events`` of the *nominal* info object are forwarded to the dataset object itself. Say the dataset with the up variation of the top mass has 300 files. We can extend the dataset above retrospectively

.. code-block:: python

   dataset_ttH_bb.set_info("mtop_up", od.DatasetInfo(
       n_files=300,
       aux=dict(mtop=173.5),
   ))

or directly in the constructor

.. code-block:: python

   dataset_ttH_bb = od.Dataset("ttH_bb", 1,
       campaign=campaign_2018,
       processes=[ttH_bb],
       info={
           "nominal": dict(n_files=1000, mtop=172.5),
           "mtop_up": dict(n_files=300, mtop=173.5),
       },
   )

Note that the dictionaries passed in ``info`` are automatically converted to a :py:class:`~order.dataset.DatasetInfo` objects, and are accessible on the dataset itself via items (``__getitem__``). Also, the example shows how to use the auxiliary data storage capabilities, that most objects in *order* provide.

.. code-block:: python

   # print the number of files in the dataset with the up-varied top quark mass
   print(dataset_ttH_bb["mtop_up"].n_files)
   # -> 300

   # also, print the respective top quark mass itself
   print(dataset_ttH_bb["mtop_up"].get_aux("mtop"))
   # -> 173.5


*Channel* and *Category*
------------------------

The typical nomenclature for distinguishing between phase space regions comprises *channels* and *categories*. The distinction between them is often somewhat arbitrary and may vary from analysis to analysis. A channel often refers to a very distinct event / data signature and when combining analyses, multiple of these channels are usually merged. In this scenario, a category describes a sub phase space of events *within* a channel.

*order* introduces the :py:class:`~order.category.Channel` and :py:class:`~order.category.Category` classes. However, as the definition above might not apply to all use cases, they can be used quite independently. They have a simple difference: while categories can have selection strings, channels cannot. This distinction might appear marginal but in some cases it turned out to be very helpful.

Categories can be (optionally) assigned to a channel. Likewise, categories are nestable:

.. code-block:: python

   import order as od

   # create a channel
   channel_e = od.Channel("e", 1,
       title="Single electron",
   )

   # create a category
   category_4j = od.Category("4j", 1,
       channel=channel_e,
       selection="nJets == 4",
       title="4 jets",
   )

   # now, the channel knows about the category and vice versa
   print(category_4j in channel_e.categories)
   # -> True

   # print the full category label
   print(category_4j.full_label)
   # -> "Single electron, 4 jets"

   # now, add a subcategory
   category_4j2b = category_4j.add_category("4j2b", 2,
       channel=channel_e,
       selection=od.util.join_root_selection(category_4j.selection, "nBTags == 2"),
       title=category_4j.title + ", 2 b-tags",
   )

   # print the selection string
   print(category_4j2b.selection)
   # -> "Single electron, 4 jets"

   # print the full category label
   print(category_4j2b.full_label)
   # -> "Single electron, 4 jets, 2 b-tags"


*Shift*
-------

A :py:class:`~order.shift.Shift` object can be used to describe a systematic uncertainty. Its name must obey a simple naming scheme: either it is ``nominal`` or it has the format ``<source>_<direction>`` where *source* can be an arbitrary string and *direction* is either ``"up"`` or ``"down"``. Also, a shift can have a type such as ``Shift.RATE``, ``Shift.SHAPE``, or ``Shift.RATE_SHAPE`` to signify exclusive rate- or shape-changing effects, or both. As usual, shifts are unqique objects.

.. code-block:: python

   import order as od

   pdf_up = od.Shift("pdf_up", 1, type=Shift.SHAPE)

   # print some properties
   print(pdf_up.name)
   # -> "pdf_up"

   print(pdf_up.source)
   # -> "pdf"

   print(pdf_up.direction)
   # -> "up"

   print(pdf_up.is_down)
   # -> False

   # "nominal" has some special behavior
   nom = od.Shift("nominal")
   print(nom.name)
   print(nom.source)
   print(nom.direction)
   # 3 x -> "nominal"


*Variable*
----------

A :py:class:`~order.variable.Variable` is supposed to provide convenience for plotting purposes. Essentially, it stores a variable expression, additional selection strings (especially useful in conjunction with categories, see above), binning helpers, axis titles, and unit information. Here are some examples:

.. code-block:: python

   import order as od

   v = od.Variable("myVar",
       expression="myBranchA * myBranchB",
       selection="myBranchC > 0",
       binning=(20, 0., 10.),
       x_title=r"$\mu p_{T}$",
       unit="GeV",
   )

   # access and print some attributes
   print(v.expression)
   # -> "myBranchA * myBranchB"

   print(v.n_bins)
   # -> 20

   print(v.even_binning)
   # -> True

   print(v.x_title_root)
   # -> "#mu p_{T}"

   print(v.full_title())
   # -> "myVar;$\mu p_{T}$" / GeV;Entries / 0.5 GeV'"

   # add further selections
   v.add_selection("myBranchD < 0", op="&&")
   print(v.selection)
   # -> "(myBranchC > 0) && (myBranchD < 0)"

   v.add_selection("myBranchE < 5", op="||")
   print(v.selection)
   # -> "((myBranchC > 0) && (myBranchD < 0)) || (myBranchE < 5)"

   # change the binning
   v.binning = [0., 1., 5., 7., 9., 10.]
   print(v.even_binning)
   # -> False

   print(v.n_bins)
   # -> 5

Variables are unique objects. However, no *id* was set in the example above. This is because variables make use of the *auto id* mechanism. The default id in the variable constructor is ``Variable.AUTO_ID`` (or simply ``"+"``), which tells order to automatically use an id that was not used before (usually the maximum of the currently used ids plus one).


Mixin classes
-------------

Within *order*, common functionality is implemented in so-called mixin classes in the :py:mod:`order.mixins` module. Examples are the handling of auxiliary data, labels, data sources (data or MC), selection strings, etc. Most classes inherit from one or (often) more mixin classes listed below.

- :py:class:`~order.mixins.CopyMixin`: Adds copy functionality.
- :py:class:`~order.mixins.AuxDataMixin`: Adds storage and access to auxiliary data.
- :py:class:`~order.mixins.TagMixin`: Adds tagging capabilities.
- :py:class:`~order.mixins.DataSourceMixin`: Adds `is_data` and `is_mc` flags.
- :py:class:`~order.mixins.SelectionMixin`: Adds selection string handling.
- :py:class:`~order.mixins.LabelMixin`: Adds labeling.
- :py:class:`~order.mixins.ColorMixin`: Adds attributes for configuring colors.


Copying objects
---------------

Most classes inherit from the :py:class:`~order.mixins.CopyMixin`. As a result, instances can be copied with Python's builtin ``copy.copy`` and ``copy.deepcopy`` methods as well as with an additional :py:meth:`~order.mixins.CopyMixin.copy` method defined on the mixin class itself.

The use of the latter is recommended as it provides better control over the copy behavior, and in fact, both ``copy.copy`` and ``copy.deepcopy`` simply call :py:meth:`~order.mixins.CopyMixin.copy` without arguments (and thus, have the identical outcome). When using :py:meth:`~order.mixins.CopyMixin.copy`, you can pass keyword arguments to configure / overwrite certain attributes of the copied object instead of copying them from the original one.

The copy mechanism can be demonstrated using :py:class:`~order.variable.Variable`'s.

.. code-block:: python

   import order as od

   jet1_pt = od.Variable("jet1_pt", 1,  # explict id
       expression="jet_pt[0]",
       unit="GeV",
       binning=[40, 0., 400.],
       x_title=r"Leading jet p_{T}",
       x_title_short=r"jet1 p_{T}",
       log_y=True,
       tags={"jet_variable"},
   )

   # copy the variable and add a selection for high pt regimes
   # attention: variables are unique objects, so we explicitely need to change
   # both name and id if we place the copied version into the same unqiqueness context
   jet1_pt_high = jet1_pt.copy("jet1_pt_high", 2,
      selection="jet_pt[0] > 200",
   )

   # now, copy the same variable, but this time change the uniqueness context,
   # so there is no need to set a different name of id
   # additional, skip copying the "tags" attribute
   with od.uniqueness_context("untagged"):
       jet1_pt_untagged = jet1_pt.copy(_skip=["tags"])

   print(jet1_pt.has_tag("jet_variable"))
   # -> True

   print(jet1_pt_untagged.has_tag("jet_variable"))
   # -> False

Checkout the API reference of the specific classes to find detailed notes on their copy behavior.


.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/riga/order/master?filepath=exampels%2Fintro.ipynb
   :alt: Open in binder
