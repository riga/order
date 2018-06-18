# -*- coding: utf-8 -*-
# flake8: noqa


__all__ = [
    "UniqueObject", "UniqueObjectIndex", "uniqueness_context", "CopyMixin", "AuxDataMixin",
    "TagMixin", "DataSourceMixin", "SelectionMixin", "LabelMixin", "ColorMixin", "Channel",
    "Category", "Variable", "Shift", "Process", "Dataset", "DatasetInfo", "Campaign", "Config",
    "Analysis", "cms",
]


# package infos
from order.__version__ import (
    __doc__, __author__, __email__, __copyright__, __credits__, __contact__, __license__,
    __status__, __version__,
)


# provisioning imports
from order.unique import UniqueObject, UniqueObjectIndex, uniqueness_context
from order.mixins import CopyMixin, AuxDataMixin, TagMixin, DataSourceMixin, SelectionMixin, \
    LabelMixin, ColorMixin
from order.categorize import Channel, Category
from order.variable import Variable
from order.shift import Shift
from order.process import Process
from order.dataset import Dataset, DatasetInfo
from order.config import Campaign, Config
from order.analysis import Analysis

# submodules
from order import cms


# LumiList
# StatModel
# Datacard


# class Datacard(object):

#     def __init__(self):
#         super(Datacard, self).__init__()

#         # bin name -> bin observation
#         self._bins = OrderedDict()

#         # process name -> dict(bin, yields)
#         self._processes = OrderedDict()

#         # shape info: file name, nominal pattern, shift pattern
#         # uses "shape" in the datacard
#         self._shapes = []

#         # shape nuisances, name -> dict(process, value)
#         # uses "lnN" in the datacard
#         self._shapeNuisances = OrderedDict()

#         # log-normal nuisances, name -> dict(process, value)
#         self._lnNuisances = OrderedDict()

#         # nuisance groups
#         self._nuisanceGroups = OrderedDict()

#         # additional lines
#         self._lines = []

#         # caches
#         self._signalIndexes = []
#         self.sep = 80 * "-"

#     @typed
#     def bins(self, bins):
#         try:
#             bins = OrderedDict(bins)
#         except:
#             raise VerboseError("invalid bins", bins)

#         for bin, observation in bins.items():
#             if not isinstance(bin, basestring):
#                 raise VerboseError("invalid bin", bin)
#             if not isinstance(observation, (float, int)):
#                 raise VerboseError("invalid observation", observation)
#             bins[str(bin)] = float(observation)

#         if self.processes and len(bins) != len(self.processes[self.processes.keys()[0]]):
#             raise Exception("length of bins does not match length of yields in processes")

#         return bins

#     def addBin(self, bin, observation):
#         bin, observation = self.__class__.bins.fparse(self, {bin: observation}).popitem()
#         self.bins[bin] = observation

#     @typed
#     def processes(self, processes):
#         try:
#             processes = OrderedDict(processes)
#         except:
#             raise VerboseError("invalid processes", processes)

#         for process, yields in processes.items():
#             if not isinstance(process, basestring):
#                 raise VerboseError("invalid process", process)
#             if isinstance(yields, (float, int)):
#                 yields = (float(yields),)
#             if isinstance(yields, (list, tuple)):
#                 if len(yields) != len(self.bins):
#                     raise VerboseError("invalid yields length", yields)
#                 yields = dict(zip(self.bins.keys(), yields))
#             elif not isinstance(yields, dict):
#                 raise VerboseError("invalid process yields", yields)
#             elif len(yields) != len(self.bins):
#                 raise VerboseError("invalid yields length", yields)
#             else:
#                 for bin, y in yields.items():
#                     if bin not in self.bins:
#                         raise VerboseError("unknown bin", bin)
#                     if not isinstance(y, (float, int)):
#                         raise VerboseError("invalid yield", y)
#                     yields[str(bin)] = float(y)
#             processes[str(process)] = yields

#         return processes

#     def addProcess(self, process, yields):
#         process, yields = self.__class__.processes.fparse(self, {process: yields}).popitem()
#         self.processes[process] = yields

#     def setSignal(self, process):
#         if isinstance(process, basestring):
#             if process not in self.processes:
#                 raise VerboseError("unknown process", process)
#             for i, _process in enumerate(self.processes):
#                 if _process == process:
#                     self._signalIndexes.append(i)
#                     break
#         elif isinstance(process, int):
#             idx = process
#             if idx >= len(self.processes):
#                 raise VerboseError("invalid process index", idx)
#             self._signalIndexes.append(idx)
#         else:
#             raise VerboseError("invalid process", process)

#     @typed
#     def shapes(self, shapes):
#         if not isinstance(shapes, (list, tuple)):
#             raise VerboseError("invalid shapes", shapes)
#         shapes = list(shapes)
#         for i, elem in enumerate(shapes):
#             if not isinstance(elem, (tuple, list)) or len(elem) != 5:
#                 raise VerboseError("invalid shapes elem", elem)
#             for val in elem:
#                 if not isinstance(val, basestring):
#                     raise VerboseError("invalid shapes value", val)
#             shapes[i] = tuple(str(val) for val in elem)

#         return shapes

#     def addShapes(self, process, channel, path, nominalPattern, shiftPattern):
#         args = [process, channel, path, nominalPattern, shiftPattern]
#         elem = self.__class__.shapes.fparse(self, [args])[0]
#         self.shapes.append(elem)

#     @typed
#     def shapeNuisances(self, nuisances):
#         try:
#             nuisances = OrderedDict(nuisances)
#         except:
#             raise VerboseError("invalid shape nuisances", nuisances)

#         for name, values in nuisances.items():
#             if not isinstance(name, basestring):
#                 raise VerboseError("invalid shape nuisance name", name)
#             if isinstance(values, (float, int, basestring)):
#                 values = len(self.processes) * [values]
#             if isinstance(values, (list, tuple)):
#                 if len(values) != len(self.processes):
#                     raise VerboseError("invald shape nuisance values length", values)
#                 values = dict(zip(self.processes.keys(), values))
#             elif not isinstance(values, dict):
#                 raise VerboseError("invalid shape nuisance values", values)
#             for process, value in values.items():
#                 if process not in self.processes:
#                     raise VerboseError("unknown process", process)
#                 if isinstance(value, basestring):
#                     if value != "-":
#                         raise VerboseError("invalid nuisance value", value)
#                     value = str(value)
#                 elif not isinstance(value, (float, int)):
#                     raise VerboseError("invalid nuisance value", value)
#                 else:
#                     value = float(value)
#                 values[str(process)] = value
#             for process in self.processes:
#                 if process not in values:
#                     values[process] = "-"
#             nuisances[str(name)] = values

#         return nuisances

#     def addShapeNuisance(self, name, values):
#         name, values = self.__class__.shapeNuisances.fparse(self, {name: values}).popitem()
#         self.shapeNuisances[name] = values

#     @typed
#     def lnNuisances(self, nuisances):
#         try:
#             nuisances = OrderedDict(nuisances)
#         except:
#             raise VerboseError("invalid ln nuisances", nuisances)

#         for name, values in nuisances.items():
#             if not isinstance(name, basestring):
#                 raise VerboseError("invalid ln nuisance name", name)
#             if isinstance(values, (float, int, basestring, tuple)):
#                 values = len(self.processes) * [values]
#             if isinstance(values, list):
#                 if len(values) != len(self.processes):
#                     raise VerboseError("invald ln nuisance values length", values)
#                 values = dict(zip(self.processes.keys(), values))
#             elif not isinstance(values, dict):
#                 raise VerboseError("invalid ln nuisance values", values)
#             for process, value in values.items():
#                 if process not in self.processes:
#                     raise VerboseError("unknown process", process)
#                 if isinstance(value, basestring):
#                     value = str(value)
#                     if value != "-":
#                         try:
#                             parts = [float(part) for part in value.split("/")]
#                             value = "%s/%s" % parts
#                         except:
#                             raise VerboseError("invalid ln nuisance value format", value)
#                 elif isinstance(value, tuple):
#                     if len(value) != 2:
#                         raise VerboseError("invalid ln nuisance format", value)
#                     if not all(isinstance(val, (float, int)) for val in value):
#                         raise VerboseError("invalid ln nuisance value", value)
#                     value = "%s/%s" % (value[1], value[0])
#                 elif isinstance(value, int):
#                     value = float(value)
#                 elif not isinstance(value, float):
#                     raise VerboseError("invalid nuisance value", value)
#                 values[str(process)] = value
#             for process in self.processes:
#                 if process not in values:
#                     values[process] = "-"
#             nuisances[str(name)] = values

#         return nuisances

#     def addLnNuisance(self, name, values):
#         name, values = self.__class__.lnNuisances.fparse(self, {name: values}).popitem()
#         self.lnNuisances[name] = values

#     @typed
#     def nuisanceGroups(self, nuisanceGroups):
#         try:
#             nuisanceGroups = OrderedDict(nuisanceGroups)
#         except:
#             raise VerboseError("invalid nuisance groups", nuisanceGroups)

#         for name, value in nuisanceGroups.items():
#             if not isinstance(name, basestring):
#                 raise VerboseError("invalid nuisance group name", name)
#             if not isinstance(value, (list, tuple)):
#                 raise VerboseError("invalid nuisance group", value)
#             else:
#                 for item in value:
#                     if item not in self.shapeNuisances and item not in self.lnNuisances:
#                         raise VerboseError("unknown nuisance", item)

#         return nuisanceGroups

#     def addNuisanceGroup(self, name, values):
#         name, values = self.__class__.nuisanceGroups.fparse(self, {name: values}).popitem()
#         self.nuisanceGroups[name] = values

#     @typed
#     def lines(self, lines):
#         if isinstance(lines, (list, tuple, set)):
#             lines = list(lines)
#         else:
#             raise VerboseError("invalid lines", lines)

#         return [str(line) for line in lines]

#     def addLine(self, line):
#         self.lines.append(str(line))

#     def dump(self, f):
#         if isinstance(f, basestring):
#             with open(f, "w") as _f:
#                 self.dump(_f)
#         else:
#             f.write(self.dumps())

#     def dumps(self):
#         card = ""

#         # header
#         card += self._tab(*self._headerData())
#         card += "\n" + self.sep + "\n"

#         # shapes
#         if self.shapes:
#             card += self._tab(*self._shapeData())
#             card += "\n" + self.sep + "\n"

#         # observation
#         card += self._tab(*self._observationData())
#         card += "\n" + self.sep + "\n"

#         # expectation
#         card += self._tab(*self._expectationData())
#         card += "\n" + self.sep + "\n"

#         # nuisances
#         if self.shapeNuisances or self.lnNuisances:
#             card += self._tab(*self._nuisanceData())

#             # nuisance groups
#             if self.nuisanceGroups:
#                 card += "\n" + "\n".join(self._nuisanceGroupData())

#         # additional lines
#         if self.lines:
#             card += "\n" + "\n".join(self.lines)

#         return card

#     def _tab(self, data, headers=()):
#         return tabulate(data, headers=headers, tablefmt="plain")

#     def _headerData(self):
#         return [
#             ("imax", len(self.bins)),
#             ("jmax", len(self.processes)-1),
#             ("kmax", len(self.shapeNuisances) + len(self.lnNuisances))
#         ],

#     def _shapeData(self):
#         return [["shapes"] + list(elem) for elem in self.shapes],

#     def _observationData(self):
#         data = []

#         # bin names
#         data.append(["bin"] + self.bins.keys())

#         # bin observations
#         data.append(["observation"] + self.bins.values())

#         return data,

#     def _expectationData(self):
#         processes, ids = self._orderedProcesses()

#         # construct data
#         data = []

#         # bin names, each name is multiplied by number processes
#         data.append(["bin"] + sum([(len(processes) * [bin]) for bin in self.bins], []))

#         # processes names, repeating for each bin
#         data.append(["process"] + processes * len(self.bins))

#         # processes ids, repeating for each bin
#         data.append(["process"] + ids * len(self.bins))

#         # simultaneously loop over bins and processes and set yields
#         totalYields = ["rate"]
#         for bin in self.bins:
#             for name in processes:
#                 yields = self.processes[name]
#                 totalYields.append(yields[bin])
#         data.append(totalYields)

#         return data,

#     def _nuisanceData(self):
#         processes = self._orderedProcesses()[0]

#         headers = ["# nuisance", "pdf"] + processes

#         data = []
#         if self.shapeNuisances:
#             data += self._shapeNuisanceData()
#         if self.lnNuisances:
#             data += self._lnNuisanceData()

#         return data, headers

#     def _shapeNuisanceData(self):
#         processes = self._orderedProcesses()[0]

#         data = []
#         for nuisance, values in self.shapeNuisances.items():
#             data.append([nuisance, "shape"] + [values[process] for process in processes])

#         return data

#     def _lnNuisanceData(self):
#         processes = self._orderedProcesses()[0]

#         data = []
#         for nuisance, values in self.lnNuisances.items():
#             data.append([nuisance, "lnN"] + [values[process] for process in processes])

#         return data

#     def _nuisanceGroupData(self):
#         data = []
#         for name, value in self.nuisanceGroups.items():
#             data.append("%s group = %s" % (name, " ".join(value)))

#         return data

#     def _orderedProcesses(self):
#         processes = self.processes.keys()

#         signalProcesses = [processes[idx] for idx in self._signalIndexes]
#         backgroundProcesses = [p for p in processes if p not in signalProcesses]

#         ids = range(-len(signalProcesses) + 1, 1)[::-1] + range(1, len(backgroundProcesses) + 1)

#         return (signalProcesses + backgroundProcesses), ids


# class Model(object):

#     def __init__(self, name, processes=None, shifts=None, shapeNuisances=None, lnNuisances=None,
#                  mcStats=False):
#         super(Model, self).__init__()

#         self._name = None
#         self.name = name

#         # process names
#         self._processes = []
#         if processes is not None:
#             self.processes = processes

#         # shift names, e.g. "jer", "jes"
#         self._shifts = ["nominal"]
#         if shifts is not None:
#             self.shifts = shifts

#         # shape nuisances
#         # name -> effect
#         self._shapeNuisances = OrderedDict()
#         if shapeNuisances is not None:
#             self.shapeNuisances = shapeNuisances

#         # log-normal nuisances
#         # name -> effect
#         self._lnNuisances = OrderedDict()
#         if lnNuisances is not None:
#             self.lnNuisances = lnNuisances

#         # flag for mcstats
#         self._mcStats = False
#         if mcStats is not None:
#             self._mcStats = mcStats

#     def __repr__(self):
#         tpl = (self.__class__.__name__, self.name, hex(id(self)))
#         return "<%s '%s' at %s>" % tpl

#     @typed
#     def name(self, name):
#         if not isinstance(name, basestring):
#             raise VerboseError("invalid name", name)
#         return str(name)

#     @typed
#     def processes(self, processes):
#         if isinstance(processes, tuple):
#             processes = list(processes)
#         elif not isinstance(processes, list):
#             raise VerboseError("invalid processes", processes)

#         for i, process in enumerate(processes):
#             if not isinstance(process, basestring):
#                 raise VerboseError("invalid process", process)
#             processes[i] = str(process)

#         return processes

#     def addProcess(self, process):
#         process = self.__class__.processes.fparse(self, [process]).pop()
#         self.processes.append(process)

#     @typed
#     def shifts(self, shifts):
#         if not isinstance(shifts, (list, tuple, set)):
#             raise VerboseError("invalid shifts", shifts)
#         shifts = list(shifts)
#         for i, shift in enumerate(shifts):
#             if not isinstance(shift, basestring):
#                 raise VerboseError("invalid shift name", shift)
#             shifts[i] = str(shift)
#         if "nominal" not in shifts:
#             raise VerboseError("missing nominal shift", shifts)
#         return shifts

#     def addShift(self, shift):
#         if not isinstance(shift, basestring):
#             raise VerboseError("invalid shift name", shift)
#         shift = str(shift)
#         if shift in self.shifts:
#             raise VerboseError("duplicate shift name", shift)
#         self.shifts.append(shift)

#     def removeShift(self, shift, silent=True):
#         if shift in self.shifts or not silent:
#             self.shifts.remove(shift)

#     @typed
#     def shapeNuisances(self, nuisances):
#         try:
#             nuisances = OrderedDict(nuisances)
#         except:
#             raise VerboseError("invalid shape nuisances", nuisances)

#         def validateValue(value):
#             if isinstance(value, (float, int)):
#                 return float(value)
#             else:
#                 raise VerboseError("invalid shape nuisance value", value)

#         for name, value in nuisances.items():
#             if not isinstance(name, basestring):
#                 raise VerboseError("invalid shape nuisance name", name)
#             if isinstance(value, dict):
#                 for key, val in value.items():
#                     value[key] = validateValue(val)
#             else:
#                 value = validateValue(value)
#             nuisances[str(name)] = value

#         return nuisances

#     def addShapeNuisance(self, name, value):
#         name, value = self.__class__.shapeNuisances.fparse(self, {name: value}).popitem()
#         if name in self.shapeNuisances or name in self.lnNuisances:
#             raise VerboseError("duplicate shape nuisance name", name)
#         self.shapeNuisances[name] = value

#     def setShapeNuisance(self, pattern, value):
#         # validate
#         pattern, value = self.__class__.shapeNuisances.fparse(self, {pattern: value}).popitem()
#         # set the value
#         names = [name for name in self.shapeNuisances if fnmatch(name, pattern)]
#         for name in names:
#             self.shapeNuisances[name] = value

#     def removeShapeNuisance(self, pattern):
#         names = [name for name in self.shapeNuisances if fnmatch(name, pattern)]
#         for name in names:
#             del self.shapeNuisances[name]

#     @typed
#     def lnNuisances(self, nuisances):
#         try:
#             nuisances = OrderedDict(nuisances)
#         except:
#             raise VerboseError("invalid ln nuisances", nuisances)

#         def validateValue(value):
#             if isinstance(value, (float, int)):
#                 return float(value)
#             elif isinstance(value, tuple):
#                 if len(value) == 2 and all(isinstance(val, (int, float)) for val in value):
#                     return value
#             else:
#                 raise VerboseError("invalid shape nuisance value", value)

#         for name, value in nuisances.items():
#             if not isinstance(name, basestring):
#                 raise VerboseError("invalid ln nuisance name", name)
#             if isinstance(value, dict):
#                 for key, val in value.items():
#                     value[key] = validateValue(val)
#             else:
#                 value = validateValue(value)
#             nuisances[str(name)] = value

#         return nuisances

#     def addLnNuisance(self, name, value):
#         name, value = self.__class__.lnNuisances.fparse(self, {name: value}).popitem()
#         if name in self.lnNuisances or name in self.shapeNuisances:
#             raise VerboseError("duplicate ln nuisance name", name)
#         self.lnNuisances[name] = value

#     def setLnNuisance(self, pattern, value):
#         # validate
#         pattern, value = self.__class__.lnNuisances.fparse(self, {pattern: value}).popitem()
#         # set the value
#         names = [name for name in self.lnNuisances if fnmatch(name, pattern)]
#         for name in names:
#             self.lnNuisances[name] = value

#     def removeLnNuisance(self, pattern):
#         names = [name for name in self.lnNuisances if fnmatch(name, pattern)]
#         for name in names:
#             del self.lnNuisances[name]

#     @typed
#     def mcStats(self, mcStats):
#         if not isinstance(mcStats, bool):
#             raise VerboseError("invalud mcStats", mcStats)

#         return mcStats

#     def clone(self, name=None, **kwargs):
#         if name is None:
#             name = self.name

#         for attr in inspect.getargspec(self.__init__).args[2:]:
#             if attr not in kwargs:
#                 kwargs[attr] = deepcopy(getattr(self, attr))

#         return self.__class__(name, **kwargs)


# class LumiList(object):

#     def __init__(self, data):
#         super(LumiList, self).__init__()

#         self._data = None
#         self.data = data

#     @classmethod
#     def read(cls, path):
#         with open(os.path.expandvars(os.path.expanduser(path)), "r") as f:
#             return cls(json.load(f))

#     @typed
#     def data(self, data):
#         if not isinstance(data, dict):
#             raise VerboseError("invalid data type", type(data))

#         _data = {}
#         for run, d in data.items():
#             try:
#                 run = int(run)
#             except ValueError:
#                 raise VerboseError("invalid lumi run number", run)
#             if not isinstance(d, dict):
#                 raise VerboseError("invalid trigger/lumi data", d)
#             _d = {}
#             for trigger, lumi in d.items():
#                 if not isinstance(trigger, basestring):
#                     raise VerboseError("invlid trigger value", trigger)
#                 if not isinstance(lumi, (int, float)):
#                     raise VerboseError("invlid lumi value", lumi)
#                 _d[str(trigger)] = float(lumi)
#             _data[run] = _d

#         return _data

#     def get(self, runRange=None, hltPath=None):
#         runs = self.data.keys()

#         # determine runs
#         if isinstance(runRange, int):
#             if runRange not in runs:
#                 return 0.
#             runs = [runRange]
#         elif isinstance(runRange, tuple) and len(runRange) == 2:
#             runs = filter(lambda run: runRange[0] <= run <= runRange[1], runs)
#         elif runRange is not None:
#             raise VerboseError("invalid run range", runRange)

#         # prepare hltPaths
#         if hltPath is not None:
#             hltPaths = makeList(hltPath)

#         # loop through runs and sum up total lumi
#         # if there are 2 or more trigger paths for a run, use the maximum value of all triggers
#         # that match hltPaths, as smaller values result from prescales
#         totalLumi = 0.
#         for run in runs:
#             runData = self.data[run]

#             # when no hltPaths are given, use all lumis
#             if hltPath is None:
#                 lumis = runData.values()
#             else:
#                 lumis = [lumi for trigger, lumi in runData.items() if multiMatch(trigger, hltPaths)]

#             if lumis:
#                 totalLumi += max(lumis)

#         return totalLumi
