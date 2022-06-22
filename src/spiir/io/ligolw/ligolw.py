import logging
from collections.abc import Iterable
from os import PathLike
from tempfile import NamedTemporaryFile

import pandas as pd
import numpy as np

from gwpy.frequencyseries import FrequencySeries

import lal.series
from ligo.lw import ligolw
import ligo.lw.array
import ligo.lw.param
import ligo.lw.table
import ligo.lw.utils

from . import postcoh

# import after postcoh.py for PostcohInspiralTable compatibility
import ligo.lw.lsctables
from gwpy.table import EventTable


logger = logging.getLogger(__name__)


# TODO:
#    - Add ilwdchar_compat for frequency series read (replace gwpy with lal.series?)
#    - Add support for lsctables (and dbtables?) modules in our ContentHandler class


@ligo.lw.array.use_in
@ligo.lw.param.use_in
@ligo.lw.table.use_in
class ILWDCharCompatContentHandler(ligolw.LIGOLWContentHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # convert all ilwd:char types to int_8s in ligolw arrays and tables
        # requires the content_handler to be instantiated with use_in decorators
        self.document = strip_ilwdchar(self.document)


def strip_ilwdchar(xmldoc: ligo.lw.ligolw.Element) -> ligo.lw.ligolw.Element:
    """Transforms a document containing tabular data using ilwd:char style row 
    IDs to plain integer row IDs. This is used to translate documents in the 
    older format for compatibility with the modern version of the LIGO Light 
    Weight XML Python library.

    This is a refactor from ligo.lw to handle ligo.lw.param.Param
    as well as ligo.lw.table.Table.

    Parameters
    ----------
    xmldoc: ligo.lw.ligolw.Element
        A valid LIGO_LW XML Document, or Element, containing the necessary
        LIGO_LW elements.

    Returns
    ----------
    ligo.lw.ligolw.Element
        The same LIGO_LW Document object passed as input with ilwd:char types
        converted to integers.

    Notes
    -----
    The transformation is lossy, and can only be inverted with specific
    knowledge of the structure of the document being processed.  Therefore,
    there is no general implementation of the reverse transformation. 
    Applications that require the inverse transformation must implement their
    own algorithm for doing so, specifically for their needs.

    """
    for elem in xmldoc.getElements(
        lambda e: (
            (e.tagName == ligo.lw.table.Table.tagName)
            or (e.tagName == ligo.lw.param.Param.tagName)
        )
    ):
        logging.info(f"{elem.tagName} {elem.Name}")

        # convert table ilwd:char column values to integers
        if elem.tagName == ligo.lw.table.Table.tagName:
            # first strip table names from column names that shouldn't have them
            if elem.Name in ligo.lw.lsctables.TableByName:
                validcolumns = ligo.lw.lsctables.TableByName[elem.Name].validcolumns
                stripped_column_to_valid_column = dict(
                    (ligo.lw.table.Column.ColumnName(name), name)
                    for name in validcolumns
                )
                for column in elem.getElementsByTagName(ligolw.Column.tagName):
                    if column.getAttribute("Name") not in validcolumns:
                        before = column.getAttribute("Name")
                        column.setAttribute(
                            "Name", stripped_column_to_valid_column[column.Name]
                        )
                        logging.info(
                            f'Renamed {elem.Name} column {before} to {column.getAttribute("Name")}.'
                        )

            # convert ilwd:char ids to integers
            idattrs = tuple(
                elem.columnnames[i]
                for i, coltype in enumerate(elem.columntypes)
                if coltype == "ilwd:char"
            )

            if not idattrs:
                logging.info("no ID columns to convert.")
                continue

            for row in elem:
                for attr in idattrs:
                    new_value = getattr(row, attr)
                    if new_value is not None:
                        setattr(row, attr, int(new_value.split(":")[-1]))

            # update the column types
            for attr in idattrs:
                elem.getColumnByName(attr).Type = "int_8s"

            logging.info(f"Converted id column(s) {', '.join(sorted(idattrs))}.")

        # convert param ilwd:char values to integers
        if elem.tagName == ligo.lw.param.Param.tagName:
            if elem.Type == "ilwd:char":
                value = getattr(elem, "value", None)
                setattr(elem, "Type", "int_8s")
                if value is not None:
                    new_value = int(value.split(":")[-1])
                    setattr(elem, "value", new_value)
                    logging.info(f"Converted param {elem.Name} value to {new_value}")
                else:
                    logging.info(f"Converted param {elem.Name}, but value is None.")

            else:
                logging.info("No param values to convert.")

    return xmldoc


def load_xmldoc(
    path: str | bytes | PathLike,
    ilwdchar_compat: bool=True,
    verbose: bool=False,
) -> ligo.lw.ligolw.Element:
    """Reads a valid LIGO_LW XML Document from a file path and returns a dictionary containing
    the complex SNR timeseries arrays associated with each interferometer ('ifo').

    Parameters
    ----------
    path: str | bytes | PathLike
        A path-like to a file containing a valid LIGO_LW XML Document.
    add_epoch_time: bool
        Whether to add the epoch time to each SNR series array for correct timestamps.
    ilwdchar_compat: bool
        Whether to add ilwdchar conversion compatibility.
    verbose: bool
        Whether to enable verbose output for ligo.lw.utils.load_filename.
    
    Returns
    -------
    ligo.lw.ligolw.Element
    """
    # define XML document parser
    if ilwdchar_compat:
        content_handler = ILWDCharCompatContentHandler
    else:

        @ligo.lw.array.use_in
        @ligo.lw.param.use_in
        @ligo.lw.table.use_in
        class ContentHandler(ligo.lw.ligolw.LIGOLWContentHandler):
            pass

        content_handler = ContentHandler

    return ligo.lw.utils.load_filename(
        path, verbose=verbose, contenthandler=content_handler
    )


def load_postcoh_tables(
    path: str | bytes | PathLike | Iterable[str | bytes | PathLike],
    columns: list[str] | None = None,
    ilwdchar_compat: bool=True,
    verbose: bool=False,
    df: bool=True,
) -> EventTable | pd.DataFrame:
    """Loads one or multiple LIGO_LW XML Documents each containing PostcohInspiralTables
    using GWPy and returns a pandas DataFrame object.

    Parameters
    ----------
    path: str | bytes | PathLike | Iterable[str | bytes | PathLike]
        A path or list of paths to LIGO_LW XML Document(s) each with a postcoh table.
    columns: list[str] | None = None
        A optional list of column names to filter and read in from each postcoh table.
    ilwdchar_compat: bool
        Whether to add ilwdchar conversion compatibility.
    verbose: bool
        Whether to enable verbose output for ligo.lw.utils.load_filename.
    df: bool
        If True returns a pd.DataFrame, else returns the original gwpy.table.EventTable.

    Returns
    -------
    pd.DataFrame
    """
    if isinstance(path, Iterable):
        # load a list of xmldoc file paths into temp files
        files = []
        for p in path:
            file = NamedTemporaryFile(mode="w")
            xmldoc = load_xmldoc(p, ilwdchar_compat, verbose)
            if ilwdchar_compat:
                xmldoc = strip_ilwdchar(xmldoc)
            xmldoc.write(file)
            file.seek(0)
            files.append(file)
        
            # construct keyword arguments for EventTable.read
            kwargs = dict(
                format="ligolw",
                tablename="postcoh",
                verbose=verbose
            )

            if columns is not None:
                # NOTE: if columns is None, read fails
                kwargs["columns"] = columns

            # load each temp file into dataframe via gwpy
            event_table = EventTable.read(files, **kwargs)

        for file in files:
            file.close()

    else:
        # load a single xmldoc
        xmldoc = load_xmldoc(path, ilwdchar_compat, verbose)

        with NamedTemporaryFile(mode="w") as file:
            if ilwdchar_compat:
                xmldoc = strip_ilwdchar(xmldoc)
            xmldoc.write(file)
            file.seek(0)

            # construct keyword arguments for EventTable
            kwargs = dict(
                format="ligolw",
                tablename="postcoh",
                verbose=verbose
            )
            if columns is not None:
                # NOTE: if columns is None, read fails
                kwargs["columns"] = columns

            # load each temp file into dataframe via gwpy
            event_table = EventTable.read(file, **kwargs)
    
    if df:
        return event_table.to_pandas()
    return event_table

def load_ligolw_frequency_series(
    path: str | bytes | PathLike, index: str = "frequency", *args, **kwargs
) -> pd.Series:
    """Reads a valid LIGO_LW XML Document from a file path and returns a pd.Series
    containing the real-valued frequency series associated with the specified kwargs.

    Uses the gwpy.frequencyseries.FrequencySeries object to read LIGO_LW XML Documents.

    Parameters
    ----------
    path: str | bytes | PathLike
        A path-like to a file containing a valid LIGO_LW XML Document.

    Returns
    -------
    pd.Series
        A pd.Series array containing the value and index of each frequency component.

    Examples
    --------
        >> ifos = ("H1", "L1", "V1")
        >> psds = {
            ifo: load_ligolw_frequency_series("coinc.xml", instrument=ifo)
            for ifo in ifos
        }
    """

    frequency_series = FrequencySeries.read(path, *args, **kwargs)
    index = pd.Index(
        np.linspace(
            start=frequency_series.f0.value,
            stop=frequency_series.df.value * len(frequency_series.value),
            num=len(frequency_series.value),
            endpoint=False,
        ),
        name="frequency",
    )
    return pd.Series(frequency_series.value, name=frequency_series.name, index=index)


def load_all_ligolw_snr_series(
    path: str | bytes | PathLike,
    add_epoch_time: bool = True,
    verbose: bool = False,
    ilwdchar_compat: bool = False,
) -> dict[int, pd.Series]:
    """Reads a valid LIGO_LW XML Document from a file path and returns a dictionary
    containing the complex SNR timeseries arrays associated with each interferometer.


    The LIGO_LW Document must contain exactly one ligo.lw.lsctables.SnglInspiralTable
    and at least one LIGO_LW COMPLEX8TimeSeries element containing the timeseries as an 
    Array named snr:array. Each row in the SnglInspiralTable should be matched to a
    corresponding COMPLEX8TimeSeries by an event_id:param.

    The returned DataFrame has columns describing each interferometer name, an index
    specifying the timestamp, and values that define the complex SNR time series array.

    Note: The true starting epoch GPS time is added to the index values of each
    pd.Series as each SNR timeseries array may not perfectly align with another.
    To undo this addition and reset all arrays to index starting from 0, simply 
    subtract the first element of the pd.Series index from every element for each
    SNR series respectively.

    Parameters
    ----------
    path: str | bytes | PathLike
        A path-like to a file containing a valid LIGO_LW XML Document.
    add_epoch_time: bool
        Whether to add the epoch time to each SNR series array for correct timestamps.
    ilwdchar_compat: bool
        Whether to add ilwdchar conversion compatibility.
    verbose: bool
        Whether to enable verbose output for ligo.lw.utils.load_filename.

    Returns
    -------
    dict[int, pd.Series]
        A dictionary of pd.Series where the key refers to the sngl_inspiral event_id,
        and the values contain the respective SNR timeseries array
        (each with their own timestamped indices).
    """
    xmldoc = load_xmldoc(path, ilwdchar_compat, verbose)

    return get_all_ligolw_snr_series_from_xmldoc(xmldoc, add_epoch_time)


def get_all_ligolw_snr_series_from_xmldoc(
    xmldoc: ligo.lw.ligolw.Element,
    add_epoch_time: bool = True,
) -> dict[int, pd.Series]:
    """Reads a valid LIGO_LW XML Document from a ligo.lw.ligolw.Document object and
    returns a dictionary containing the complex SNR timeseries arrays associated with
    each interferometer ('ifo').

    The LIGO_LW Document must contain exactly one ligo.lw.lsctables.SnglInspiralTable 
    and at least one LIGO_LW COMPLEX8TimeSeries element containing the timeseries as an
    Array named snr:array. Each row in the SnglInspiralTable should be matched to a
    corresponding COMPLEX8TimeSeries by an event_id:param.

    The returned DataFrame has columns describing each interferometer name, an
    index specifying the timestamp, and values that define the complex SNR time series.

    Note: The true starting epoch GPS time is added to the index values of each
    pd.Series as each SNR timeseries array may not perfectly align with another.
    To undo this addition and reset all arrays to index starting from 0, simply
    subtract the first element of the pd.Series index from every element for each
    SNR series respectively.

    Parameters
    ----------
    xmldoc: ligo.lw.ligolw.Element
        A LIGO_LW XML Document, or Element, containing the necessary LIGO_LW elements.
    add_epoch_time: bool
        Whether to add the epoch time to each SNR series array for correct timestamps.

    Returns
    -------
    dict[int, pd.Series]
        A dictionary of pd.Series where the key refers to the sngl_inspiral event_id,
        and the values contain the respective SNR timeseries array
        (each with their own timestamped indices).
    """

    # get inspiral rows from sngl_inspiral table
    sngl_inspiral_table = ligo.lw.table.Table.get_table(xmldoc, name="sngl_inspiral")

    # get SNR series from LIGO_LW elements
    data = {}
    for elem in xmldoc.getElements(
        lambda e: (
            (e.tagName == "LIGO_LW")
            and (e.hasAttribute("Name"))
            and (e.Name == "COMPLEX8TimeSeries")
        )
    ):
        # get event_id param
        params = elem.getElements(
            lambda e: (
                (e.tagName == ligo.lw.param.Param.tagName)
                and (e.getAttribute("Name") == "event_id:param")
            )
        )
        assert len(params) == 1, "Expected only one param argument to match conditions."
        event_id = params[0].value

        # match snr series event_id:param with sngl_inspiral event_id
        sngl_inspiral = list(
            filter(lambda row: row.event_id == event_id, sngl_inspiral_table)
        )
        assert (
            len(sngl_inspiral) == 1
        ), "Expected only one sngl_inspiral to match conditions."
        ifo = sngl_inspiral[0].ifo

        # build SNR time series array
        snr = lal.series.parse_COMPLEX8TimeSeries(elem)
        num = len(snr.data.data)
        timesteps = np.linspace(
            start=0.0, stop=snr.deltaT * num, num=num, endpoint=False
        )
        if add_epoch_time:
            timesteps += float(snr.epoch)

        # build complex snr as a pandas Series object
        data[event_id] = pd.Series(
            data=snr.data.data, index=pd.Index(timesteps, name="time"), name=ifo
        )

    return data
