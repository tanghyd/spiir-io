# SPIIR I/O Utilities Package

Author: Daniel Tang [Last Updated: 22/06/2022]

## Installation

We recommend first installing Python3 in a virtual environment of your choice.

### Virtualenv

Then, for example, a venv based virtual environment would use:

    python -m venv venv
    . venv/bin/activate
    pip install --upgrade pip setuptools wheel  # optional
    pip install -r requirements.txt
    pip install -e .

### Conda

A conda environment would be created with:

    conda create -n venv python=3.x  # pick your version
    conda activate venv
    pip install --upgrade pip setuptools wheel  # optional
    pip install -r requirements.txt
    pip install -e .


## Usage

A pandas DataFrame object can be constructed for a LIGOLW XML Document file path.

    import spiir
    df = spiir.io.ligolw.load_postcoh_tables("zerolag.xml")

The same also works for a list of zerolag xml files.

    from pathlib import Path
    import spiir

    zerolags = list(Path("data").glob("*_zerolag_*.xml"))
    df = spiir.io.ligolw.load_postcoh_tables(zerolags)