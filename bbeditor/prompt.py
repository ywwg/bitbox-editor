"""prompt.py
Like, handle all the possible commands and stuff


TODO: make this all chomp-style parsing.  we first chomp the command,
Then the command can chomp a set of coords or a filename or whatever.
Gets tricky with swap which can take one or two sets of coords

It also looks like state belongs in the handler, not here.

"""
import glob
import os.path

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

import bbeditor.handlers as handlers

class Prompt(object):
  def __init__(self, herstory_file):
    self._herstory = FileHistory(herstory_file)
    self._handler = handlers.Handler()
    self._root = None
    self._cur_preset = None
    self._cur_clip = {'track': None, 'clip':None}

  def do_prompt(self):
    """Returns false if asked to quit."""

    text = prompt('bitbox-editor (? for help) > ', history=self._herstory)

    if text == '?':
      self.help()
      return True
    elif text == 'q':
      return False
    elif text.startswith('dir'):
      self._root = self.handle_dir(text)
      return True

    if not self._root:
      print ("Please set 'dir foo/bar' for bitbox directory")
      return True

    if text.startswith('c'):
      self._cur_preset = self.choose_preset(text)
      if self._cur_preset is not None:
        self._handler.list_preset(self._root, self._cur_preset, self._cur_clip)
      return True

    if text.startswith('l'):
      self.list_presets()
      return True

    if not self._cur_preset:
      print ('Please choose a preset with c')
      return True

    if text.startswith('p'):
      self._cur_clip = self._choose_clip(text)
      if self._cur_clip is not None:
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif text.startswith('f'):
      self.handle_fix(text)
    elif text.startswith('m '):
      self.move_preset(text)
    elif text.startswith('r'):
      self.handle_rename(text)
    elif text.startswith('s'):
      self.handle_swap(text)
    elif text == 'norm':
      self._cur_clip = self._choose_clip(text)
      if self._cur_clip is not None:
        self._handler.normalize_clip(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif text == 'normall':
      self._handler.normalize_preset(self._root, self._cur_preset)
    elif text == 'trim':
      self._cur_clip = self._choose_clip(text)
      if self._cur_clip is not None:
        self._handler.trim_clip(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif text == 'trimall':
      self._handler.trim_all(self._root, self._cur_preset)
    elif text == 'mono':
      self._cur_clip = self._choose_clip(text)
      if self._cur_clip is not None:
        self._handler.clip_to_mono(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif text.startswith('undo'):
      self._cur_clip = self._choose_clip(text)
      if self._cur_clip is not None:
        self._handler.undo_clip(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    else:
      self.help()

    self._handler.list_preset(self._root, self._cur_preset, self._cur_clip)
    return True

  def help(self):
    print ('Known commands:')
    print ('')
    print ('  dir     # set which dir the bitbox files are in')
    print ('  l       # list presets')
    print ('  c       # choose current preset by name')
    print ('  m       # move preset to new name')
    print ('  p       # play a clip for the current preset: X,Y')
    print ('  f       # fix a clip with a bad filename')
    print ('  r       # rename clip, specify coords and new name (can include subdir)')
    print ('  s       # swap clips, specify two sets of coords: 0,0 1,2')
    print ('  norm    # Normalize a single clip')
    print ('  normall # Normalize a whole preset by an equal amount per clip')
    print ('  trim    # trim start and end of clip to zero crossings for better looping (EXPERIMENTAL)')
    print ('  trimall # trim all clips in preset (EXPERIMENTAL)')
    print ('  mono    # convert to mono (BROKEN)')
    print ('  q       # quit')

  def handle_dir(self, text):
    """Parses out which directory the user specified and returns it.

    Returns None if not a valid dir
    """
    tokens = text.split(' ')
    if len(tokens) == 1:
      print ('current path: %s' % self._root)
      return None

    path = text.split(' ', 1)[1]
    if not os.path.isdir(path):
      print ('bad path: %s' % path)
      return None
    return path

  def list_presets(self):
    for f in sorted(glob.glob(os.path.join(self._root, "*.xml"))):
      print (os.path.basename(f))

  def choose_preset(self, text):
    """Parses text and extracts preset name

    Returns:
      valid preset string or None on invalid input
    """

    preset_name = text.split(' ', 1)[1]
    if not os.path.isfile(os.path.join(self._root, '%s.xml' % preset_name)):
      print ("Didn't find preset %s" % (preset_name))
      return None

    return preset_name

  def move_preset(self, text):
    """Moves preset filename (renaming preset)"
    """
    new_name = text.split(' ', 1)[1].upper()

    if self._handler.move_preset(self._root, self._cur_preset, new_name):
      self._cur_preset = new_name

  def _parse_coords(self, text):
    """Parses a comma-separated pair of ints and does valiation.

    Returns: a tuple of two ints, or None on error
    """
    def print_error():
      print ('Expected coordinates after command, like: 0,0')

    coords = text.split(',')
    if len(coords) != 2:
      print_error()
      return None

    track_num = int(coords[0])
    if track_num < 0 or track_num > 3:
      print_error()
      return None
    clip_num = int(coords[1])
    if clip_num < 0 or clip_num > 3:
      print_error()
      return None

    return {'track': track_num, 'clip': clip_num}

  def _choose_clip(self, text):
    """Parses text and figures out which clip was chosen

    Returns None on error
    """
    def print_error():
      print ('Expected coordinates after command, like: 0,0')

    tokens = text.split(' ', 1)
    if len(tokens) == 1 or not tokens[1]:
      # Handle case where it's a bare p command
      if self._cur_clip['track'] is not None:
        return self._cur_clip
    if len(tokens) != 2:
      print_error()
      return None

    coords = self._parse_coords(tokens[1])
    if coords is None:
      return
    if not self._handler.get_clip(self._root, self._cur_preset, coords):
      print ('No clip at that position')
      return None
    self._cur_clip = coords
    return coords

  def handle_fix(self, text):
    tokens = text.split(' ', 2)
    if len(tokens) == 2:
      # if we have a clip selected we can just rename it
      if self._cur_clip['track'] is not None and tokens[1].upper().endswith('.WAV'):
        self._handler.rename_clip(
            self._root, self._cur_preset, self._cur_clip, tokens[1])
        return
    elif len(tokens) != 3:
      print_error()
      return

    coords = self._parse_coords(tokens[1])
    if coords is None:
      return
    if not self._handler.get_clip(self._root, self._cur_preset, coords):
      print ('No clip at that position')
      return
    self._cur_clip = coords

    self._handler.rename_clip(self._root, self._cur_preset, self._cur_clip, tokens[2])

  def handle_rename(self, text):
    def print_error():
      print ('Expected coordinates and new filename, like: 0,0 foo/bar/baz.wav')
      print ('Or just a new filename if clip is selectedm like: foo/bar/baz.wav')

    tokens = text.split(' ', 2)
    if len(tokens) == 2:
      # if we have a clip selected we can just rename it
      if self._cur_clip['track'] is not None and tokens[1].upper().endswith('.WAV'):
        self._handler.move_clip(
            self._root, self._cur_preset, self._cur_clip, tokens[1])
        return
    elif len(tokens) != 3:
      print_error()
      return

    coords = self._parse_coords(tokens[1])
    if coords is None:
      return
    if not self._handler.get_clip(self._root, self._cur_preset, coords):
      print ('No clip at that position')
      return
    self._cur_clip = coords

    self._handler.move_clip(self._root, self._cur_preset, self._cur_clip, tokens[2])

  def handle_swap(self, text):
    def print_error():
      print ('Expected two sets of coordinates, like: 0,0 1,2')
      print ('Or one set if already selected')

    tokens = text.split(' ', 3)
    this_clip = {'track': None, 'clip':None, 'filename': ''}
    other_clip = {'track': None, 'clip':None, 'filename': ''}
    if len(tokens) == 3:
      other_clip = self._parse_coords(tokens[2])
      if other_clip is None:
        print_error()
        return
      this_clip = self._parse_coords(tokens[1])
      if this_clip is None:
        print_error()
        return
    elif len(tokens) == 2:
      if self._cur_clip['track'] is None or self._cur_clip['clip'] is None:
        print_error()
        return
      this_clip = self._cur_clip
      other_clip = self._parse_coords(tokens[1])
    else:
      print_error()
      return

    this_clip['filename'] = self._handler.get_clip(self._root, self._cur_preset, this_clip)
    if not this_clip['filename']:
      this_clip['filename'] = ''
      self._cur_clip = this_clip
    other_clip['filename'] = self._handler.get_clip(self._root, self._cur_preset, other_clip)
    if not other_clip['filename']:
      other_clip['filename'] = ''
      self._cur_clip = other_clip

    self._handler.rename_clip(self._root, self._cur_preset, other_clip, this_clip['filename'])
    self._handler.rename_clip(self._root, self._cur_preset, this_clip, other_clip['filename'])
