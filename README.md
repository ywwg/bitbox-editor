# Bitbox Editor

(UNOFFICIAL)

(UNSUPPORTED)

(REALLY, MAKE A BACKUP OF YOUR DATA!)

Bitbox Editor is a stupid interactive python terminal tool for mucking about
with the XML and sample files on a 1010Music BitBox.  It can do a bunch of
useful things like:

* Rename, move, and reorganize clips within a preset
* Rename presets
* Conversion to mono for clips (BROKEN)
* Normalize single clips or a group of clips relative to each other
* Keeps a basic history of commands for faster use

## Important Caveat

Any operations that involve editing audio data (normalize, mono conversion)
downsample to 16bit!  If you are uncomfortable with this loss of quality don't
use this tool.

## Another Important Caveat

Conversion to mono is broken in pydub master, so don't use it.

## Commands

* **dir**: Set which dir the bitbox files are in
* **l**: List presets
* **c**: Choose current preset by name
* **m**: Move preset to new name
* **p**: Play a clip for the current preset: X,Y
* **f**: Fix a clip with a bad filename
* **r**: Rename clip, specify coords and new name (can include subdir)
* **s**: Swap clips, specify two sets of coords: 0,0 1,2
* **norm**: Normalize a single clip
* **normall**: # Normalize a whole preset by an equal amount per clip
* **mono**: Convert to mono (BROKEN in pydub master)
* **undo**: Restore a clip from its most recent backup
* **q**:    Quit

## Example Use

**Set the location of your bitbox data and list the presets**

```
bitbox-editor (? for help) > dir /media/yourname/thumbdrive
bitbox-editor (? for help) > l
Presets in /media/yourname/thumbdrive:
My Track 1
New Preset 2
Whatever
```

**Choose a preset and play the first clip**

```
bitbox-editor (? for help) > c My Track 1
Preset My Track 1:
 0,0: 130\08\BKICK01.WAV
 0,1: 130\08\BKICK02.WAV
 0,2:
 0,3:
 1,0: 130\08\SMACK01.WAV
 1,1: 130\08\midsmack01.wav
 1,2: 130\08\midsmack02.wav
 1,3: 130\08\hismack02.wav
 2,0: 130\08\revsmack01.wav
 2,1:
 2,2: 130\08\revsmack02.wav
 2,3:
 3,0: 130\08\RIM01.WAV
 3,1:
 3,2:
 3,3:

bitbox-editor (? for help) > p 0,0
Input #0, wav, from '/tmp/tmpsqtq184f.wav':   0KB sq=    0B f=0/0
  Duration: 00:00:01.85, bitrate: 1536 kb/s
    Stream #0:0: Audio: pcm_s16le ([1][0][0][0] / 0x0001), 48000 Hz, 2 channels, s16, 1536 kb/s
   1.83 M-A:  0.000 fd=   0 aq=    0KB vq=    0KB sq=    0B f=0/0
```

**Normalize the clip**

Because we already selected a clip we don't need to say which one we want to
normalize.

```
bitbox-editor (? for help) > norm
```

**Oh no that broke for some reason!**

```
bitbox-editor (? for help) > undo
```

## Installation

I'm keeping this vague because this tool isn't really ready for general users
yet.  If you know what pip is, you can figure out how to install these things.

Deps (pipable):

* python3
* prompt_toolkit
* pydub

Of course deps have deps too!
