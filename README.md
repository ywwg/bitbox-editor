# Bitbox Editor

(UNOFFICIAL)

(UNSUPPORTED)

(REALLY, MAKE A BACKUP OF YOUR DATA!)

Bitbox Editor is a stupid interactive python terminal tool for mucking about
with the XML and sample files on a 1010Music BitBox.  It can do a bunch of
useful things like:

* Rename, move, and reorganize clips within a preset
* Basic normalization and conversion to mono for clips
* Normalize a group of clips relative to each other

## Commands

* dir     # Set which dir the bitbox files are in
* l       # List presets
* c       # Choose current preset by name
* m       # Move preset to new name
* p       # Play a clip for the current preset: X,Y
* f       # Fix a clip with a bad filename
* r       # Rename clip, specify coords and new name (can include subdir)
* s       # Swap clips, specify two sets of coords: 0,0 1,2
* norm    # Normalize a single clip
* normall # Normalize a whole preset by an equal amount per clip
* mono    # Convert to mono (BROKEN in pydub master)
* undo    # Restore a clip from its most recent backup
* q       # Quit


Deps (pipable):

* python3
* prompt_toolkit
* pydub

Of course deps have deps too!
