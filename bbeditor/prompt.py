"""prompt.py
Like, handle all the possible commands and stuff


TODO: make this all chomp-style parsing.  we first chomp the command,
Then the command can chomp a set of coords or a filename or whatever.
Gets tricky with swap which can take one or two sets of coords

It also looks like state belongs in the handler, not here.

"""
import fnmatch
import glob
import os.path
import re
import shutil

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory

import bbeditor.handlers as handlers

class Error(Exception):
  """Base class for exceptions in this module."""
  pass

class InvalidCoordinates(Error):
  pass

class BBCompleter(Completer):
  """Handles completions for commands.

  Needs access to the parent prompt for certain operations, and has its own Handler when it
  needs access to information about the preset.
  """

  def __init__(self, prompt):
    self._prompt = prompt
    self._handler = handlers.Handler()

  def get_completions(self, document, complete_event):
    command = self._prompt.parse_command(document.current_line_before_cursor)
    # Completion for choosing a new preset
    if command['command'] == 'c':
      if command['arg']:
        for p in self._prompt.list_presets():
          if p.startswith(command['arg']):
            yield Completion(p, start_position=0-len(command['arg']))
    # Completion for specifying coordinates
    elif not command['coords'] and self._prompt.get_cur_preset():
      root = self._prompt.get_root()
      preset = self._prompt.get_cur_preset()
      # Match partial coordinates
      coord_matcher = re.compile(r'[0-3],?$')
      if coord_matcher.match(command['arg']):
        for x, track in enumerate(self._handler.get_clips_filenames(root, preset)):
          for y, clip in enumerate(track):
            coords = '%d,%d' % (x,y)
            # If this slot has a clip in it and it matches the partial coordinates, offer completion
            if clip and coords.startswith(command['arg']):
              yield Completion(coords, start_position=0-len(command['arg']))


class Prompt(object):
  XML_MATCHER = re.compile(fnmatch.translate('*.xml'), re.IGNORECASE)

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
          print ('Presets in %s:' % self._root)
          print ('\n'.join(self.list_presets()))
        break
    self._cur_preset = None
    self._cur_clip = {'track': None, 'clip':None}

  def get_root(self):
    return self._root

  def get_cur_preset(self):
    return self._cur_preset

  def do_prompt(self):
    """Returns false if asked to quit."""

    text = prompt('bitbox-editor (? for help) > ', history=self._herstory, completer=BBCompleter(self))
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
        self.show_current_preset()
      return True

    if command['command'] == 'l':
      print ('Presets in %s:' % self._root)
      print ('\n'.join(self.list_presets()))
      return True
    if command['command'] == 'exportv1':
      self.export_v1()
      return True

    if not self._cur_preset:
      print ('Please choose a preset with c')
      return True

    if command['command'] == 'p':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self.play_current_clip()
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
        self.play_current_clip()
    elif command['command'] == 'normall':
      self._handler.normalize_preset(self._root, self._cur_preset)
    elif command['command'] == 'trim':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.trim_clip(self._root, self._cur_preset, self._cur_clip)
        self.play_current_clip()
    elif command['command'] == 'trimall':
      self._handler.trim_all(self._root, self._cur_preset)
    elif command['command'] == 'mono':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.clip_to_mono(self._root, self._cur_preset, self._cur_clip)
        self.play_current_clip()
    elif command['command'] == 'undo':
      self._cur_clip = self._choose_clip(command)
      if self._cur_clip is not None:
        self._handler.undo_clip(self._root, self._cur_preset, self._cur_clip)
        self.play_current_clip()
    else:
      self.help()

    self.show_current_preset()

    return True

  def help(self):
    print ('Known commands:')
    print ('')
    print ('  dir      # set which dir the bitbox files are in')
    print ('  l        # list presets')
    print ('  c        # choose current preset by name')
    print ('  m        # move preset to new name')
    print ('  p        # play a clip for the current preset: X,Y')
    print ('  f        # fix a clip with a bad filename')
    print ('  r        # rename clip, specify coords and new name (can include subdir)')
    print ('  s        # swap clips, specify two sets of coords: 0,0 1,2')
    print ('  norm     # Normalize a single clip')
    print ('  normall  # Normalize a whole preset by an equal amount per clip')
    print ('  trim     # trim start and end of clip to zero crossings for better looping (EXPERIMENTAL)')
    print ('  trimall  # trim all clips in preset (EXPERIMENTAL)')
    print ('  mono     # convert to mono (BROKEN in pydub master)')
    print ('  undo     # restore a clip from its most recent backup')
    print ('  exportv1 # Export the first 12 xml files in the directory as old-style ' +
           'SE000001.xml presets for use on older firmwares')
    print ('  q        # quit')

  def _parse_coords(self, text):
    """Parses a comma-separated pair of ints and does valiation.

    Returns: a tuple of two ints, or None on error

    Throws: InvalidCoordinates if it looks like coordinates but is invalid.
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
      raise InvalidCoordinates(text)
    if clip_num < 0 or clip_num > 3:
      raise InvalidCoordinates(text)

    return {'track': track_num, 'clip': clip_num}

  def parse_command(self, text):
    """Takes a raw command and returns a dictionary to describe it.

    Commands are of the form:
      [command] (coords...) (string argument)

    Where coords are zero or more int pairs like '3,4' (no quotes needed).

    If the coords are out of bounds they won't be returned, which could cause
    problems for things like: norm 3,6 because it'll just return norm and
    operate on the current clip.

    Returns:
      dict: {
        'command':  the command specified
        'coords': a List of coordinates, usually one
        'arg': a List of remaining arguments
      }
    """
    command = {
      'command': '',
      'coords': [],
      'arg': '',
    }

    found_cmd = False
    found_noncoord = False
    while text:
      space_idx = text.find(' ')
      if space_idx == -1:
        t = text
        text = ''
      else:
        t = text[:space_idx]
        text = text[space_idx + 1:]

      if not t.strip():
        continue

      if not found_cmd:
        command['command'] = t.strip()
        found_cmd = True
        continue

      try:
        coords = self._parse_coords(t)
      except InvalidCoordinates:
        return {
            'command': '',
            'coords': [],
            'arg': '',
          }
      if coords is not None:
        if found_noncoord:
          # Coords after args are invalid.
          return {
            'command': '',
            'coords': [],
            'arg': '',
          }
        command['coords'].append(coords)
        continue

      if found_noncoord:
        continue

      found_noncoord = True
      command['arg'] = t
      if text:
        command['arg'] += ' ' + text
    return command

  def handle_dir(self, command):
    """Parses out which directory the user specified and returns it.

    Returns None if not a valid dir
    """

    if not command['arg']:
      print ('current path: %s' % self._root)
      return None

    path = command['arg']

    if not os.path.isdir(path):
      print ('bad path: %s' % path)
      return None
    return path

  def list_presets(self):
    """Return all the files in the root with .xml extensions"""
    xmls = []
    for f in os.listdir(self._root):
      if self.XML_MATCHER.match(f):
        xmls.append(os.path.splitext(os.path.basename(f))[0])
    return xmls

  def play_current_clip(self):
    try:
      self._handler.play_clip(self._root, self._cur_preset, self._cur_clip)
    except handlers.NoClipError:
      print ('No clip at that position')
    except handlers.FileNotFound as e:
      print ('File not found: %s' % e.filename)
      print ('(Case sensitive issue?  Try fix)')
      return

  def show_current_preset(self):
    """Lists clips in given preset"""
    clips = self._handler.get_clips_filenames(self._root, self._cur_preset)
    print ('')
    print ('Preset %s:' % self._cur_preset)
    for tracknum in range(0, 4):
      for clipnum in range(0, 4):
        if (self._cur_clip is not None and
            tracknum == self._cur_clip['track'] and
            clipnum == self._cur_clip['clip']):
          print ('*', end='')
        else:
          print (' ', end='')
        print ('%d,%d: %s' % (tracknum, clipnum, clips[tracknum][clipnum]))

  def export_v1(self):
    xmls = [f for f in os.listdir(self._root) if self.XML_MATCHER.match(f)]
    for i, f in enumerate(sorted(xmls)[:12]):
      print ("exporting" + f)
      oldpath = os.path.join(self._root, f)
      newpath = os.path.join(self._root, 'SE%06d.XML' % (i + 1))
      print ('Copying %s to %s' % (oldpath, newpath))
      shutil.copy(oldpath, newpath)

  def choose_preset(self, command):
    """Parses text and extracts preset name

    Returns:
      valid preset string or None on invalid input
    """

    if not command['arg']:
      print ('Wrong number of arguments, want one preset name')
      return None

    preset_name = command['arg']
    if not os.path.isfile(os.path.join(self._root, '%s.xml' % preset_name)):
      print ("Didn't find preset: '%s'" % (preset_name))
      return None

    return preset_name

  def move_preset(self, command):
    """Moves preset filename (renaming preset)"
    """

    if not command['arg']:
      print ('Wrong number of arguments, want a new preset name')
      return None

    if self._cur_preset is None:
      print ('No preset selected, select one to rename')
      return None

    new_name = command['arg']
    try:
      self._handler.move_preset(self._root, self._cur_preset, new_name)
      self._cur_preset = new_name
    except handlers.NoClipError:
      print ('No clip at that position')
    except handlers.FileNotFound as e:
      print ('Source file does not exist: %s' % e.filename)
    except handlers.FileAlreadyExists as e:
      print ('Destination file already exists: %s' % e.filename)
    except handlers.MkdirError as e:
      print ('Error creating dir for %s: %s' % (e.path, e.err))
    except handlers.FileMoveError as e:
      print ('Error moving file: %s' % e.err)

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

    if len(command['coords']) == 1:
      self._choose_clip(command)

    if self._cur_clip is None:
      print ('Need to select a clip')
      return

    if not command['arg']:
      print ('Need a new filename to rename to')
      return

    correctname = command['arg']
    try:
      self._handler.repoint_clip(self._root, self._cur_preset, self._cur_clip, correctname)
    except handlers.FileNotFound as e:
      print ('New filename does not exist, repoint failed: %s' % e.filename)

  def handle_rename(self, command):
    """Rename clip filename on disk.

    Unlike fix above, this renames the file on disk as well as updates the XML.
    """
    def print_error():
      print ('Expected coordinates and new filename, like: 0,0 foo/bar/baz.wav')
      print ('Or just a new filename if clip is selected like: foo/bar/baz.wav')

    if len(command['coords']) == 1:
      self._choose_clip(command)

    if self._cur_clip is None:
      print_error()
      return

    if not command['arg']:
      print_error()
      return

    newname = command['arg']
    try:
      self._handler.move_clip(self._root, self._cur_preset, self._cur_clip, newname)
    except handlers.NoClipError:
      print ('No clip at that position')
    except handlers.FileNotFound as e:
      print ('Source file does not exist: %s' % e.filename)
    except handlers.FileAlreadyExists as e:
      print ('Destination file already exists: %s' % e.filename)
    except handlers.MkdirError as e:
      print ('Error creating dir for %s: %s' % (e.path, e.err))
    except handlers.FileMoveError as e:
      print ('Error moving file: %s' % e.err)

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

    self._handler.swap_clips(self._root, self._cur_preset, this_clip, other_clip)
