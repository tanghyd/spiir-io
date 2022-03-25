import glue.ligolw
from glue.ligolw import dbtables, table
import ligo.lw.lsctables

from lal import LIGOTimeGPS
from xml.sax.xmlreader import AttributesImpl
import six

# TO DO:
# - Unify approach for handling python-ligo-lw and glue.ligolw
# - Port compatibility with C postcoh table
# - Check compatibility with dbtables

# dbtables.ligolwtypes.ToPyType["ilwd:char"] = six.text_type

PostcohInspiralID = glue.ligolw.ilwd.get_ilwdchar_class("postcoh", "event_id")


class PostcohInspiralTable(glue.ligolw.table.Table):
    tableName = "postcoh"
    validcolumns = {
        "process_id": "ilwd:char",
        "event_id": "ilwd:char",
        "end_time": "int_4s",
        "end_time_ns": "int_4s",
        "end_time_L": "int_4s",
        "end_time_ns_L": "int_4s",
        "end_time_H": "int_4s",
        "end_time_ns_H": "int_4s",
        "end_time_V": "int_4s",
        "end_time_ns_V": "int_4s",
        "snglsnr_L": "real_4",
        "snglsnr_H": "real_4",
        "snglsnr_V": "real_4",
        "coaphase_L": "real_4",
        "coaphase_H": "real_4",
        "coaphase_V": "real_4",
        "chisq_L": "real_4",
        "chisq_H": "real_4",
        "chisq_V": "real_4",
        "is_background": "int_4s",
        "livetime": "int_4s",
        "ifos": "lstring",
        "pivotal_ifo": "lstring",
        "tmplt_idx": "int_4s",
        "bankid": "int_4s",
        "pix_idx": "int_4s",
        "cohsnr": "real_4",
        "nullsnr": "real_4",
        "cmbchisq": "real_4",
        "spearman_pval": "real_4",
        "fap": "real_4",
        "far_h": "real_4",
        "far_l": "real_4",
        "far_v": "real_4",
        "far_h_1w": "real_4",
        "far_l_1w": "real_4",
        "far_v_1w": "real_4",
        "far_h_1d": "real_4",
        "far_l_1d": "real_4",
        "far_v_1d": "real_4",
        "far_h_2h": "real_4",
        "far_l_2h": "real_4",
        "far_v_2h": "real_4",
        "far": "real_4",
        "far_2h": "real_4",
        "far_1d": "real_4",
        "far_1w": "real_4",
        "skymap_fname": "lstring",
        "template_duration": "real_8",
        "mass1": "real_4",
        "mass2": "real_4",
        "mchirp": "real_4",
        "mtotal": "real_4",
        "spin1x": "real_4",
        "spin1y": "real_4",
        "spin1z": "real_4",
        "spin2x": "real_4",
        "spin2y": "real_4",
        "spin2z": "real_4",
        "eta": "real_4",
        "f_final": "real_4",
        "ra": "real_8",
        "dec": "real_8",
        "deff_L": "real_8",
        "deff_H": "real_8",
        "deff_V": "real_8",
        "rank": "real_8",
    }
    constraints = "PRIMARY KEY (event_id)"
    next_id = PostcohInspiralID(0)


class PostcohInspiral(glue.ligolw.table.Table.RowType):
    __slots__ = list(PostcohInspiralTable.validcolumns.keys())

    @property
    def end(self):
        if self.end_time is None and self.end_time_ns is None:
            return None
        return LIGOTimeGPS(self.end_time, self.end_time_ns)

    @end.setter
    def end(self, gps):
        if gps is None:
            self.end_time = self.end_time_ns = None
        else:
            self.end_time, self.end_time_ns = gps.gpsSeconds, gps.gpsNanoSeconds


PostcohInspiralTable.RowType = PostcohInspiral

# ref: glue.ligolw.lsctables
# Override portions of a lsctables.LIGOLWContentHandler class
#

TableByName = {PostcohInspiralTable.tableName: PostcohInspiralTable}


def use_in(ContentHandler):
    """
    Modify ContentHandler, a sub-class of
    glue.ligolw.LIGOLWContentHandler, to cause it to use the Table
    classes defined in this module when parsing XML documents.

    Example:

    >>> from glue.ligolw import ligolw
    >>> class MyContentHandler(ligolw.LIGOLWContentHandler):
    ...	pass
    ...
    >>> use_in(MyContentHandler)
    <class 'glue.ligolw.lsctables.MyContentHandler'>
    """
    # need to comment out the next clause in case there are other use_in performed
    # e.g. lsctables.use_in before this use_in
    # ContentHandler = table.use_in(ContentHandler)

    def startTable(self, parent, attrs, __orig_startTable=ContentHandler.startTable):
        name = glue.ligolw.table.Table.TableName(attrs["Name"])
        if name in TableByName:
            return TableByName[name](attrs)
        return __orig_startTable(self, parent, attrs)

    ContentHandler.startTable = startTable
    return ContentHandler


# the code below (gwpy and lsctables) should be improved, i.e. integrated directly
# however, we also have the problem that we are using legacy glue.ligolw
# we should consider how these changes should be handled with python-ligo-lw

# add our custom postcoh table to the lsctables.TableByName dict
glue.ligolw.lsctables.TableByName.update(TableByName)
ligo.lw.lsctables.TableByName.update(TableByName)

# Example:
# >>> from glue.ligolw import lsctables
# >>> "postcoh" in lsctables.TableByName
# False
# >>> import spiir.io.ligolw.postcoh
# >>> "postcoh" in lsctables.TableByName
# True
