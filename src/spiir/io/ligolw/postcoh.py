from ligo.lw import ligolw, lsctables, table, utils

from lal import LIGOTimeGPS

# TO DO:
# - Unify approach for handling python-ligo-lw and glue.ligolw
# - Port compatibility with C postcoh table
# - Check compatibility with dbtables

# database compatibility for ilwd:char - review this
# from glue.ligolw import dbtables
# dbtables.ligolwtypes.ToPyType["ilwd:char"] = six.text_type

# PostcohInspiralID = utils.ilwd.get_ilwdchar_class(u"postcoh", u"event_id")

class PostcohInspiralTable(table.Table):
    tableName = "postcoh"
    validcolumns = {
        "process_id": "int_8s",
        "event_id": "int_8s",
        "end_time": "int_4s",
        "end_time_ns": "int_4s",
        "end_time_sngl_H1": "int_4s",
        "end_time_ns_sngl_H1": "int_4s",
        "end_time_sngl_L1": "int_4s",
        "end_time_ns_sngl_L1": "int_4s",
        "end_time_sngl_V1": "int_4s",
        "end_time_ns_sngl_V1": "int_4s",
        "snglsnr_H1": "real_4",
        "snglsnr_L1": "real_4",
        "snglsnr_V1": "real_4",
        "coaphase_L1": "real_4",
        "coaphase_H1": "real_4",
        "coaphase_V1": "real_4",
        "chisq_H1": "real_4",
        "chisq_L1": "real_4",
        "chisq_V1": "real_4",
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
        "far_sngl_H1": "real_4",
        "far_sngl_L1": "real_4",
        "far_sngl_V1": "real_4",
        "far_1w_sngl_H1": "real_4",
        "far_1w_sngl_L1": "real_4",
        "far_1w_sngl_V1": "real_4",
        "far_1d_sngl_H1": "real_4",
        "far_1d_sngl_L1": "real_4",
        "far_1d_sngl_V1": "real_4",
        "far_2h_sngl_H1": "real_4",
        "far_2h_sngl_L1": "real_4",
        "far_2h_sngl_V1": "real_4",
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
        "deff_H1": "real_8",
        "deff_L1": "real_8",
        "deff_V1": "real_8",
        "rank": "real_8",
    }
    constraints = "PRIMARY KEY (event_id)"
    # next_id = PostcohInspiralID(0)


class PostcohInspiral(table.Table.RowType):
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
        name = ligolw.Table.TableName(attrs[u"Name"])
        if name in TableByName:
            return TableByName[name](attrs)
        return __orig_startTable(self, parent, attrs)

    ContentHandler.startTable = startTable
    return ContentHandler


# the code below (gwpy and lsctables) should be improved, i.e. integrated directly
# however, we also have the problem that we are using legacy glue.ligolw
# we should consider how these changes should be handled with python-ligo-lw

# add our custom postcoh table to the lsctables.TableByName dict
lsctables.TableByName.update(TableByName)

# Example:
# >>> from glue.ligolw import lsctables
# >>> "postcoh" in lsctables.TableByName
# False
# >>> import spiir.io.ligolw.postcoh
# >>> "postcoh" in lsctables.TableByName
# True

