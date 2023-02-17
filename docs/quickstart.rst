Quickstart
==========

The sections below explain the most important classes, the concept of mixins and some notes on copying objects.
Open the `intro.ipynb <https://github.com/riga/order/blob/master/examples/intro.ipynb>`__ notebook to see these classes in action or run it interactively on colab or binder:

|colab| |binder|

*order* follows a very strict API design and naming scheme.

1. Methods start with (or at least contain) verbs. E.g. setters and getters are prefixed with ``set_`` and ``get_``, respectively.
2. Properties implement type checks and, where applicable, conversions! Assigments such as ``my_object.some_string_attribute = 123`` (can) immediately fail. This way, type ambiguities during analysis execution are avoided and detected early.
3. The code style is `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`__ compatible (checked via `flake8 <https://pypi.org/project/flake8/>`__).


*UniqueObject* and *UniqueObjectIndex*
--------------------------------------

Before diving into the actual physics-related classes, it is necessary to understand their primary underlying base class: :py:class:`~order.unique.UniqueObject`.

A :py:class:`~order.unique.UniqueObject` essentially has two attributes: a *name* (string) and an *id* (integer).
Within the same *index*, implemented by :py:class:`~order.unique.UniqueObjectIndex`, **both** *name* and *id* are ensured to be unique.
Therefore, the mechanism unambiguously assigns

1. a human-readable name to objects (e.g.) for expressive use on the command-line, and
2. a unique identifier to objects (e.g.) for encoding information in data structures such as ROOT trees.

Consider this example implementation of a physics process that is assigned to a dataset, which holds in index of processes.

.. code-block:: python

    import order as od

    dataset = od.Dataset(name="tt_powheg", id=1)
    process = od.Process(name="tt", id=1)

    # add process to dataset
    dataset.add_process(process)

Now, when creating another process with either the same name or id and trying to add it to the dataset, an exception will be raised.

.. code-block:: python

    process_same_name = od.Process(name="tt", id=2)
    process_same_id = od.Process(name="dy", id=1)

    dataset.add_process(process_same_name)
    # -> DuplicateNameException

    dataset.add_process(process_same_id)
    # -> DuplicateIdException

The :py:class:`~order.unique.UniqueObjectIndex` provides various convenience methods to add, extend, remove or lookup objects.

.. code-block:: python

    # dataset.processes is an index that stores od.Process objects

    dataset.processes.get("tt")
    # -> <Process at 0x10340d250, name=tt, id=1>

    1 in dataset.processes
    # -> True

    "tt" in dataset.processes
    # -> True

    "dy" in dataset.processes
    # -> False

    dataset.processes.n.tt  # lookup by the name proxy "n"
    # -> <Process at 0x10340d250, name=tt, id=1>

    len(dataset.processes)
    # -> 1

    dataset.processes.clear()
    len(dataset.processes)
    # -> 0

As most classses within *order* inherit from :py:class:`~order.unique.UniqueObject` or have one or more :py:class:`~order.unique.UniqueObjectIndex`'s, you will find similar constructs all across the API.


*Analysis*, *Campaign* and *Config*
-----------------------------------

An instance of the :py:class:`~order.analysis.Analysis` class represents the overarching object containing information of a physics analysis.

Varying requirements across data-taking periods, complex sub measurements, or simply different revisions of the same analysis are typical reasons why the structuring of information is quite demanding over the course of an analysis with sometimes unpredictable incidents and deadlines (code ↔︎ time uncertainty is a thing).
For this purpose, *order* introduces two classes: :py:class:`~order.config.Campaign` and :py:class:`~order.config.Config`.

A :py:class:`~order.config.Campaign` describes and contains **analysis-independent** information, such as detector alignment settings, event simulation settings, recorded / simulated datasets, etc.
In general, a pre-configured campaign object could be provided centrally by a working group or collaboration.

A :py:class:`~order.config.Config` object holds **analysis-dependent** information related to a certain campaign.
Thus, a config is unambiguously assigned to both an analysis and a campaign.

Consider, for example, offline triggers that are used to select events specifically in one analysis.
By construction, they should not be stored in a campaign object (which is **analysis-independent**), but they might also change between different data-taking periods and therefore should not be stored in the analysis object itself.
Instead, a config object is an ideal place for such information.

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

Besides a *name* and an *id*, a :py:class:`~order.process.Process` object has cross sections for different center-of-mass energies, labels and colors for plotting purposes, and information about whether or not it describes real data or MC (it inherits from the :py:class:`~order.mixins.DataSourceMixin`, see `mixin classes <mixin-classes>`__).
Cross section values are automatically converted to `scinum.Number <https://scinum.readthedocs.io/en/latest/#number>`__ instances, which are able to store multiple uncertainties, provide automatic error propagation and also support NumPy arrays.

Moreover, processes can have subprocesses and *order* provides convenience methods to work with arbitrarily deep process lookup.

.. code-block:: python

    import order as od
    from scinum import Number, UP, DOWN

    ttH = od.Process(
        name="ttH",
        id=1,
        xsecs={
            13: Number(0.5071, {
                "scale": (0.058j, 0.092j),  # relative scale uncertainty of +5.8/-9.2 %
                "pdf"  : 0.036j,            # relative pdf uncertainty of +-3.6 %
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
    ttH_bb = ttH.add_process(
        name="ttH_bb",
        id=2,
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

Information about datasets is stored in :py:class:`~order.dataset.Dataset` objects.
Standard attributes are *name* and *id*, labels, and data/MC information.
Optionally, a dataset can be assigned to a :py:class:`~order.config.Campaign` and to one or more :py:class:`~order.process.Process` objects.
Let's extend the above example:

.. code-block:: python

    dataset_ttH_bb = od.Dataset(
        name="ttH_bb",
        id=1,
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
    # -> ["<Dataset at 0x1169421d0, name=ttH_bb, id=1>"]

    # print the number of files
    print(datasaet_ttH_bb.n_files)
    # -> 1000

The last statement prints the number of files in that dataset.
But what happens when systematic variations exist for that dataset?
Let's assume there are two variants that were generated with different top quark masses.
Do we create two additional datasets?
**No**.
They are stored in the same dataset object.

A dataset stores :py:class:`~order.dataset.DatasetInfo` objects, containing information that may vary (e.g.) across systematic uncertainties.
Examples are the number of files, the number of total events, or arbitrary auxiliary information (see the :py:class:`~order.mixins.AuxDataMixin` in the `mixin classes <mixin-classes>`__ below).
In fact, the number of files ``n_files`` above is already stored in a :py:class:`~order.dataset.DatasetInfo` object, stored as ``dataset_ttH_bb.info["nominal"]``.
The attributes ``n_files`` and ``n_events`` of the *nominal* info object are forwarded to the dataset object itself.
Say the dataset with the up variation of the top mass has 300 files.
We can extend the dataset above retrospectively

.. code-block:: python

    dataset_ttH_bb.set_info("mtop_up", od.DatasetInfo(
        n_files=300,
        aux=dict(mtop=173.5),
    ))

or directly in the constructor

.. code-block:: python

    dataset_ttH_bb = od.Dataset(
        name="ttH_bb",
        id=1,
        campaign=campaign_2018,
        processes=[ttH_bb],
        info={
            "nominal": dict(n_files=1000, mtop=172.5),
            "mtop_up": dict(n_files=300, mtop=173.5),
        },
    )

Note that the dictionaries passed in ``info`` are automatically converted to a :py:class:`~order.dataset.DatasetInfo` objects, and are accessible on the dataset itself via items (``__getitem__``).
Also, the example shows how to use the auxiliary data storage capabilities, that most objects in *order* provide.

.. code-block:: python

    # print the number of files in the dataset with the up-varied top quark mass
    print(dataset_ttH_bb["mtop_up"].n_files)
    # -> 300

    # also, print the respective top quark mass itself
    print(dataset_ttH_bb["mtop_up"].get_aux("mtop"))
    # -> 173.5


*Channel* and *Category*
------------------------

The typical nomenclature for distinguishing between phase space regions comprises *channels* and *categories*.
The distinction between them is often somewhat arbitrary and may vary from analysis to analysis.
A channel often refers to a very distinct event / data signature and when combining analyses, multiple of these channels are usually merged.
In this scenario, a category describes a sub phase space of events *within* a channel.

*order* introduces the :py:class:`~order.category.Channel` and :py:class:`~order.category.Category` classes.
However, as the definition above might not apply to all use cases, they can be used quite independently.
They have a simple difference: while categories can have selection strings, channels cannot.
This distinction might appear marginal but in some cases it turned out to be very helpful.

Categories can be (optionally) assigned to a channel.
Likewise, categories are nestable:

.. code-block:: python

    import order as od

    # create a channel
    channel_e = od.Channel(
        name="e",
        id=1,
        title="Single electron",
    )

    # create a category
    category_4j = od.Category(
        name="4j",
        id=1,
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
    category_4j2b = category_4j.add_category(
        name="4j2b",
        id=2,
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

A :py:class:`~order.shift.Shift` object can be used to describe a systematic uncertainty.
Its name must obey a simple naming scheme: either it is ``nominal`` or it has the format ``<source>_<direction>`` where *source* can be an arbitrary string and *direction* is either ``"up"`` or ``"down"``.
Also, a shift can have a type such as ``Shift.RATE``, ``Shift.SHAPE``, or ``Shift.RATE_SHAPE`` to signify exclusive rate- or shape-changing effects, or both.
As usual, shifts are unqique objects.

.. code-block:: python

    import order as od

    pdf_up = od.Shift(name="pdf_up", id=1, type=Shift.SHAPE)

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

A :py:class:`~order.variable.Variable` is supposed to provide convenience for plotting purposes.
Essentially, it stores a variable expression, additional selection strings (especially useful in conjunction with categories, see above), binning helpers, axis titles, and unit information.
Here are some examples:

.. code-block:: python

    import order as od

    v = od.Variable(
        name="myVar",
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

Variables are unique objects.
However, no *id* was set in the example above.
This is because variables make use of the *auto id* mechanism.
The default id in the variable constructor is ``Variable.AUTO_ID`` (or simply ``"+"``), which tells order to automatically use an id that was not used before (usually the maximum of the currently used ids plus one).


Mixin classes
-------------

Within *order*, common functionality is implemented in so-called mixin classes in the :py:mod:`order.mixins` module.
Examples are the handling of auxiliary data, labels, data sources (data or MC), selection strings, etc.
Most classes inherit from one or (often) more mixin classes listed below.

- :py:class:`~order.mixins.CopyMixin`: Adds copy functionality.
- :py:class:`~order.mixins.AuxDataMixin`: Adds storage and access to auxiliary data.
- :py:class:`~order.mixins.TagMixin`: Adds tagging capabilities.
- :py:class:`~order.mixins.DataSourceMixin`: Adds `is_data` and `is_mc` flags.
- :py:class:`~order.mixins.SelectionMixin`: Adds selection string handling.
- :py:class:`~order.mixins.LabelMixin`: Adds labeling.
- :py:class:`~order.mixins.ColorMixin`: Adds attributes for configuring colors.


Copying objects
---------------

Most classes inherit from the :py:class:`~order.mixins.CopyMixin`.
As a result, instances can be copied via :py:meth:`~order.mixins.CopyMixin.copy`, returning a full, deep copy including relations to other objects, or via :py:meth:`~order.mixins.CopyMixin.copy_shallow` which copies everything *but* those relations.
You can pass keyword arguments to configure / overwrite certain attributes of the copied object instead of copying them from the original one.

The copy mechanism can be demonstrated using :py:class:`~order.variable.Variable`'s.

.. code-block:: python

    import order as od

    jet1_pt = od.Variable(
        name="jet1_pt",
        id=1,  # explict id
        expression="jet_pt[0]",
        unit="GeV",
        binning=[40, 0., 400.],
        x_title=r"Leading jet p_{T}",
        x_title_short=r"jet1 p_{T}",
        log_y=True,
        tags={"jet_variable"},
    )

    # copy the variable and add a selection for high pt regimes
    jet1_pt_high = jet1_pt.copy(
       name="jet1_pt_high",
       id=2,
       selection="jet_pt[0] > 200",
    )

    # copy the variable with same name and id, but overwrite the tags attribute
    jet1_pt_untagged = jet1_pt.copy(tags=[])

    print(jet1_pt.has_tag("jet_variable"))
    # -> True

    print(jet1_pt_untagged.has_tag("jet_variable"))
    # -> False

Checkout the API reference of the specific classes to find detailed notes on their copy behavior.

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/riga/order/blob/master/examples/intro.ipynb
   :alt: Open in colab

.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/riga/order/master?filepath=examples%2Fintro.ipynb
   :alt: Open in binder
