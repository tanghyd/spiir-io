# SPIIR Software Package

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
we have to add our table manually (see `spiir.io.ligolw.postcoh.py#L150`). In order for
modules like `gwpy` to recognise the `PostcohInspiralTable` schema, we must first import
this package before `gwpy` as follows:

Note: you may need to install `gwpy` and `pandas` in your virtual environment first.

    # import packages in correct order
    import spiir.io.ligolw.postcoh
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

## Design Principles

- We want all SPIIR functionality to be contained in an importable Python package.
- We want to self-contain data generation processes separately to the search pipeline.
- We may optionally want to install pipelines with different search implementations.
- There should be options to use some pipelines in either "batch" or "stream" mode.

We want the core of the data processing in the spiir repository to be implemented in numpy
with "batched" vectorised operations and easy integration with Cython, TensorFlow, and PyTorch.

On installation, the user can specify whether they want to install optional search
submodules that have dependencies from GStreamer, TensorFlow, PyTorch, CUDA etc.

Implementing pipeline components as decoupled submodules that are still compatible
with an overarching numpy processing backbone should help with development flexibility.

### Draft Package Structure

A complete SPIIR install with all sub-modules would have the import structure below:

    spiir/
    
        io/                    # concern: input and output of data
            ligolw/                     # definitions for custom ligolw types
                postcoh.py         
                utils.py                # multiprocessing tools, etc.
            frames/                     # maybe move io.frames => io. ?
                gwf.py
                hdf.py
            gracedb/
            kafka/
            hpc/                        # hpc utils (only if significant annd useful)
                ozstar.py
                condor.py

        templates/             # concern: approximating astrophysical signals
            parameters/                 # input parameters for simulation models
            waveforms/                  # for template approximation and ML training
            iir/                        # gstlal-spiir.python.spiirbank refactor
            banks/                      # banks may be agnostic to templates used
            
        strain/                # concern: processing on interferometer strains
            psd/                        # used for online PSD estimation as well
            gating/                     # data quality & state vector components?
            far/                        # false alarm rate => maybe move to search/

        search/                # concern: determining signal from noise in "strains"

            filter/                     # matched filtering - i.e. produce SNR
                gstlal-spiir/           ### SUBMODULE # importable python module
                torch-spiir/            ### SUBMODULE # refactor from gst => pytorch
                damon_net/              ### SUBMODULE # damon deep learning SNR model 

            classify/          # concern: astrophysical source classification
                fgmc/                   ### SUBMODULE
                vortega/                ### SUBMODULE # mass contour method 
                
            localise/          # concern: generating skymaps
                spiir/                  # standard SPIIR method for skymap
                gwnet/                  ### SUBMODULE # chayan deep learning model 
                bayestar.py             # wrapper to run BAYESTAR from ligo.skymap?

            veto/              # concern: noise classification to reject candidates
                idq.py                  

        events/                # concern: handling results from searches (?)
            candidates/
            catalog/

        deployment/            # concern: observation runs (==> /bin? or ==> .io?)

        ml/                    # concern: utilities for mlops etc. (move .ml => .io?)
            torch/                     # shared utils for torch models (optional?)
                stream/                # stream dataloaders for deployment
                batch/                 # batch dataloaders for training
            tf/                        # same as torch for tensorflow

### Hypothetical Future Usage

Some ideas for Python pseudocode structure that would handle SPIIR search logic.

```
    # example use of multiple pipeline implementations
    from spiir.templates.bank import Bank
    from spiir.strain.psds import get_default_psds
    
    from spiir.search import gstlal_spiir, torch_spiir
    from spiir.search.localisation import LocalisationNeuralNetwork

    # load initial conditions for spiir search pipeline
    psds = get_default_psds()

    bank = Bank()  # distributed data loader?
    templates = bank.get_templates()

    ## SNR models

    # GStreamer GPU pipeline encapsulated in Python
    # model = gstlal_spiir.pipeline(templates, psds)

    #  OR torch model on GPU
    device = torch.device("cuda")  # could be CPU too
    model = torch_spiir.pipeline(templates, psds, device=device)

    # localisation model
    gwnet = LocalisationNeuralNetwork(device=device)

    # pseudo-code example: online (stream mode)?
    with open("kafka:stream") as stream:  # async?
        # SNR matched filtering
        event = await model(stream)

        if ranking_statistic(event, far) >= 0.5:
            # localisation
            skymaps = await gwnet(events)
            gracedb.upload()


    # pseudo-code example: offline (batch mode)
    dataloader = DataLoader()
    model.train()
    for data in dataloader:
        events = model(data)
        loss = loss_func(events, ground_truth)
        loss.backward()


```
