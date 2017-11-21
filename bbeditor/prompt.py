"""prompt.py
Like, handle all the possible commands and stuff


TODO: make this all chomp-style parsing.  we first chomp the command,
Then the command can chomp a set of coords or a filename or whatever.
Gets tricky with swap which can take one or two sets of coords

It also looks like state belongs in the handler, not here.

"""
import glob
import os.path
import shlex

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

import bbeditor.handlers as handlers

class Prompt(object):
  def __init__(self, herstory_file):
    self._herstory = FileHistory(herstory_file)
    self._handler = handlers.Handler()

    self._root = None
    for l in reversed(self._herstory):
      command = self.parse_command(l)
      if command['command'] == 'dir':
        path = self.handle_dir(command)
        if path is not None:
          self._root = path
          self.list_presets()
        break
    self._cur_preset = None
    self._cur_clip = {'track': None, 'clip':None}

  def do_prompt(self):
    """Returns false if asked to quit."""

    text = prompt('bitbox-editor (? for help) > ', history=self._herstory)
    command = self.parse_command(text)

    if command['command'] == '?':
      self.help()
      return True
    elif command['command'] == 'q':
      return False
    elif command['command'] == 'dir':
      self._root = self.handle_dir(command)
      return True

    if not self._root:
      print ("Please set 'dir foo/bar' for bitbox directory")
      return True

    if command['command'] == 'c':
      self._cur_preset = self.choose_preset(command)
      if self._cur_preset is not None:
        self._handler.list_preset(self._root, self._cur_preset, self._cur_clip)
      return True

    if command['command'] == 'l':
      self.list_presets()
      return True

    if not self._cur_preset:
      print ('Please choose a preset with c')
      return True

    self._handler.list_preset(self._root, self._cur_preset, self._cur_clip)

    if command['command'] == 'p':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif command['command'] == 'f':
      self.handle_fix(command)
    elif command['command'] == 'm':
      self.move_preset(command)
    elif command['command'] == 'r':
      self.handle_rename(command)
    elif command['command'] == 's':
      self.handle_swap(command)
    elif command['command'] == 'norm':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.normalize_clip(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif command['command'] == 'normall':
      self._handler.normalize_preset(self._root, self._cur_preset)
    elif command['command'] == 'trim':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.trim_clip(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif command['command'] == 'trimall':
      self._handler.trim_all(self._root, self._cur_preset)
    elif command['command'] == 'mono':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.clip_to_mono(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    elif command['command'] == 'undo':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.undo_clip(self._root, self._cur_preset, self._cur_clip)
        self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    else:
      self.help()

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
    print ('  mono    # convert to mono (BROKEN in pydub master)')
    print ('  undo    # restore a clip from its most recent backup')
    print ('  q       # quit')
    print ('')
    print ('If your argument has spaces, put quotes around it!')

  def _parse_coords(self, text):
    """Parses a comma-separated pair of ints and does valiation.

    Returns: a tuple of two ints, or None on error
    """
    coords = text.split(',')
    if len(coords) != 2:
      return None

    (track_num, clip_num) = (0, 0)
    try:
      track_num = int(coords[0])
      clip_num = int(coords[1])
    except ValueError:
      return None

    if track_num < 0 or track_num > 3:
      return None
    if clip_num < 0 or clip_num > 3:
      return None

    return {'track': track_num, 'clip': clip_num}

  def parse_command(self, text):
    """Takes a raw command and returns a dictionary to describe it

    Returns:
      dict: {
        'command':  the command specified
        'coords': a List of coordinates, usually one
        'arg': a List of remaining arguments
      }
    """
    tokens = shlex.split(text)
    command = {
      'command': tokens[0],
      'coords': [],
      'args': [],
    }
    if len(tokens) == 1:
      return command
    for t in tokens[1:]:
      t = t.strip()
      if len(t) == 0:
        continue
      coords = self._parse_coords(t)
      if coords is not None:
        command['coords'].append(coords)
        continue
      command['args'].append(t)
    return command


  def handle_dir(self, command):
    """Parses out which directory the user specified and returns it.

    Returns None if not a valid dir
    """

    if len(command['args']) == 0:
      print ('current path: %s' % self._root)
      return None

    if len(command['args']) > 1:
      print ('Too many arguments, want a single path.')
      print ('(remember to quote spaced paths)')
      return None

    path = command['args'][0]

    if not os.path.isdir(path):
      print ('bad path: %s' % path)
      return None
    return path

  def list_presets(self):
    """Show all the files in the root with .xml extensions"""
    print ('Presets in %s:' % self._root)
    for f in sorted(glob.glob(os.path.join(self._root, "*.xml"))):
      print (os.path.basename(f))

  def choose_preset(self, command):
    """Parses text and extracts preset name

    Returns:
      valid preset string or None on invalid input
    """

    if len(command['args']) != 1:
      print ('Wrong number of arguments, want one preset name')
      print ('(remember to quote spaced names)')
      return None

    preset_name = command['args'][0]
    if not os.path.isfile(os.path.join(self._root, '%s.xml' % preset_name)):
      print ("Didn't find preset: '%s'" % (preset_name))
      return None

    return preset_name

  def move_preset(self, command):
    """Moves preset filename (renaming preset)"
    """

    if len(command['args']) == 0:
      print ('Wrong number of arguments, want a new preset name')
      print ('(remember to quote spaced names)')
      return None

    if self._cur_preset is None:
      print ('No preset selected, select one to rename')
      return None

    new_name = command['args'][0]
    if self._handler.move_preset(self._root, self._cur_preset, new_name):
      self._cur_preset = new_name

  def _choose_clip(self, command):
    """Set the currently chosen clip as long as there is one at this position

    Returns None on error
    """
    def print_error():
      print ('Expected coordinates after command, like: 0,0')

    if len(command['coords']) == 0:
      # Handle case where it's a bare command
      if self._cur_clip['track'] is not None:
        return self._cur_clip

    if len(command['coords']) != 1:
      print_error()
      return None

    coords = command['coords'][0]
    if not self._handler.get_clip(self._root, self._cur_preset, coords):
      print ('No clip at that position')
      return None
    self._cur_clip = coords
    return coords

  def handle_fix(self, command):
    """Fix a bad filename in the XML, usually due to case sensitivity issues.

    This just changes the text in the XML, it doesn't change any files on disk.
    """
    def print_error():
      print ('Expected coordinates and correct filename, like: 0,0 foo/bar/baz.wav')
      print ('Or just a new filename if clip is selected like: foo/bar/baz.wav')
      print ('(remember to quote spaced filenames)')

    if len(command['coords']) == 1:
      self._choose_clip(command)

    if self._cur_clip is None:
      print ('Need to select a clip')
      return

    if len(command['args']) != 1:
      print ('Need a new filename to rename to')
      return

    correctname = command['args'][0]
    self._handler.repoint_clip(self._root, self._cur_preset, self._cur_clip, correctname)

  def handle_rename(self, command):
    """Rename clip filename on disk.

    Unlike fix above, this renames the file on disk as well as updates the XML.
    """
    def print_error():
      print ('Expected coordinates and new filename, like: 0,0 foo/bar/baz.wav')
      print ('Or just a new filename if clip is selected like: foo/bar/baz.wav')
      print ('(remember to quote spaced filenames)')

    if len(command['coords']) == 1:
      self._choose_clip(command)

    if self._cur_clip is None:
      print_error()
      return

    if len(command['args']) != 1:
      print_error()
      return

    newname = command['args'][0]
    self._handler.move_clip(self._root, self._cur_preset, self._cur_clip, newname)

  def handle_swap(self, command):
    def print_error():
      print ('Expected two sets of coordinates, like: 0,0 1,2')
      print ('Or one set if already selected')

    if len(command['coords']) == 0:
      print_error()
      return
    if len(command['coords']) == 1:
      if self._cur_clip['track'] is None or self._cur_clip['clip'] is None:
        print_error()
        return
      this_clip = self._cur_clip
      other_clip = command['coords'][0]
    elif len(command['coords']) == 2:
      this_clip = command['coords'][0]
      other_clip = command['coords'][1]
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

    # repoint just changes the XML, so nothing changes on disk (and we don't
    # do something stupid like overwrite one clip with the other).
    self._handler.repoint_clip(self._root, self._cur_preset, other_clip, this_clip['filename'])
    self._handler.repoint_clip(self._root, self._cur_preset, this_clip, other_clip['filename'])
