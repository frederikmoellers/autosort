# autosort

Automatically sort documents into the folder structure

## Who is this for?

People who have a structured folder hierarchy where they keep all their
documents like invoices, bank statements etc.

## How do I use this?

Copy some example sorters into the `sorters` directory. Adapt the code as
necessary to work on *your* documents and to sort into *your* folder structure.

Then, run `autosort.py` with the relevant parameters to sort new files.

## Will this overwrite/delete my files?

Not unless you tell it to. Before overwriting existing files, `autosort` will
ask you for confirmation and display the target filename in red. It should be
mostly safe for testing.

More documentation to come…
