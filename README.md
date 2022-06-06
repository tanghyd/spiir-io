# SPIIR Software Utilities Package

Author: Daniel Tang

Last Updated: 25/03/22

## Installation

We recommend first installing Python3 in a virtual environment of your choice, which
should work perfectly fine for Python3.6 to Python3.8 (from testing).

For example, a venv based virtual environment would use:

    python3 -m venv venv  # python may already be python3, depending on your install
    . venv/bin/activate
    python -m pip install --upgrade pip  # optional

A conda environment would be created with:

    conda create -n venv python=3.x  # pick your version
    conda activate venv
    python -m pip install --upgrade pip  # optional

Then this local package can be installed inside the virtual environment with:

    git clone https://github.com/tanghyd/spiir.git && cd spiir
    pip install -e .


## Usage

As of 25/03/22, the only functionality of this package is to provide utilities to
handle SPIIR's `PostcohInspiralTable` in Python3 - in particular we have written a workaround
to include this custom table in the list of available lsctables.

As we have not integrated this with `python-ligo-lw` and `gwpy` modules directly,
we have to add our table manually (see `spiir.utils.ligolw.postcoh.py#L150`). In order for
modules like `gwpy` to recognise the `PostcohInspiralTable` schema, we must first import
this package before `gwpy` as follows:

Note: you may need to install `gwpy` and `pandas` in your virtual environment first.

    # import packages in correct order
    import spiir.utils.ligolw.postcoh
    import gwpy.table

    # load an EventTable with gwpy (kwarg format="ligolw" is handled automatically)
    event_table = gwpy.table.EventTable.read("zerolag.xml", tablename="postcoh")
    df = event_table.to_pandas()

The same should apply for direct usage with `glue.ligolw.lsctables`.

### Common Errors

#### Module Import Ordering

The following error triggered on `astropy.table.Table` is expected if you import `spiir`
in the wrong order, as the `gwpy.table.EventTable` derives from the `astropy` table.
The cause is due to the fact it does not recognise the custom `PostcohInspiralTable` and
does not handle its input properly. The tail end of this error is shown below:

    File "/usr/lib/python3.8/site-packages/gwpy/table/io/ligolw.py", line 422, in read_table
        return Table(read_ligolw_table(source, tablename=tablename, **read_kw),
    File "/usr/lib/python3.8/site-packages/astropy/table/table.py", line 726, in __init__
        raise TypeError('__init__() got unexpected keyword argument {!r}'
    TypeError: __init__() got unexpected keyword argument 'rename'

#### Python3.10

We tried testing this package on a modern Python3.10 installation but ran into some
compatibility errors with ilwd:char types with `ligol.lw.ligolw`. While its likely this
may have been due to an incorrect installation or build, it's also possible that support
for the legacy format of ligolw may have been deprecated in the more modern versions of
these package dependencies. The tail end of this error is shown below:

    ligo.lw.ligolw.ElementError: line 14: invalid type 'ilwd:char' for Column 'process_id' in Table 'process', expected type 'int_8s'

Fixes would include modern and legacy format handling for `ilwd:char` types, or
deprecating the legacy version of the `PostcohInspiralTable` for more modern formats.
For now, any feedback on package compatibility from users running Python versions
above Python3.8 would be appreciated.