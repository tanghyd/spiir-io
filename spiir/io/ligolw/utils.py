# Copyright (C) 2020 Leo Singer, 2021 Tito Dal Canton
#
# Modified March 2022 by Daniel Tang
# Source: https://github.com/gwastro/pycbc/blob/master/pycbc/io/ligolw.py

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tools for dealing with LIGOLW XML files."""

from typing import Union

# modern format
from ligo.lw import lsctables as ligolw_lsctables
from ligo.lw.table import Column as ligolw_Column

# legacy format
from glue.ligolw import lsctables as glue_lsctables
from glue.ligolw.table import Column as glue_Column


def default_null_value(col_name: str, col_type: str) -> Union[float, int, str]:
    """
    Associate a sensible "null" default value to a given LIGOLW column type.
    """
    if col_type in ["real_4", "real_8"]:
        return 0.0

    elif col_type in ["int_4s", "int_8s"]:
        # this case includes row IDs
        return 0

    # for handling legacy spiir sngl_inspiral ids
    elif col_type in ["ilwd:char"]:
        # return "sngl_inspiral:{col_name}:0"
        return ""

    elif col_type == "lstring":
        return ""

    else:
        raise NotImplementedError(
            f"Do not know how to initialize column {col_name} of type {col_type}"
        )


def get_empty_sngl_inspiral(
    nones: bool = False,
    legacy: bool = False,
):
    """
    Function to create a SnglInspiral object where all columns are populated
    but all are set to values that test False (ie. strings to '', floats/ints
    to 0, ...). This avoids errors when you try to create a table containing
    columns you don't care about, but which still need populating.

    NOTE: This will also produce a process_id and event_id with 0 values.
    For most applications these should be set to their correct values.

    Parameters
    ----------
        nones : bool (False)
            If True, just set all columns to None.
        kwargs : dict
            User specified key value pairs that can be used to set table defaults.

    Returns
    --------
        lsctables.SnglInspiral
            The "empty" SnglInspiral object.
    """

    # get ligolw table specification
    if legacy:
        sngl = glue_lsctables.SnglInspiral()
        cols = glue_lsctables.SnglInspiralTable.validcolumns
        column = glue_Column
    else:
        sngl = ligolw_lsctables.SnglInspiral()
        cols = ligolw_lsctables.SnglInspiralTable.validcolumns
        column = ligolw_Column

    # set column defaults
    for entry in cols:
        col_name = column.ColumnName(entry)
        value = None if nones else default_null_value(col_name, cols[entry])
        setattr(sngl, col_name, value)

    return sngl
