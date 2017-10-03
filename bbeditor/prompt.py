"""prompt.py
Like, handle all the possible commands and stuff
"""
import io
import os.path
import pathlib
import shutil
import xml.sax

import bbeditor.bbxml as bbxml
import bbeditor.playback as playback
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

class Prompt(object):
  def __init__(self, herstory_file):
    self._dir = None
    self._player = playback.Player()
    self._herstory = FileHistory(herstory_file)
    self._cur_preset = None

  def do_prompt(self):
    """Returns false if asked to quit."""

    text = prompt('(? for help) > ', history=self._herstory)

    if text == '?':
      self.help()
      return True
    elif text == 'q':
      return False
    elif text.startswith('dir'):
      self._dir = self.handle_dir(text)
      return True

    if not self._dir:
      print ("Please set 'dir foo/bar' for bitbox directory")
      return True

    if text.startswith('c'):
      self._cur_preset = self.choose_preset(text)
      self.list_preset(self._cur_preset)
      return True

    if not self._cur_preset:
      print ('Please choose a preset with s')
      return True

    if text.startswith('p'):
      self.play_clip(self._cur_preset, text)
    elif text.startswith('r'):
      self.rename_clip(self._cur_preset, text)
    elif text:
      self.help()
      return True

    self.list_preset(self._cur_preset)

    return True

  def help(self):
    print ('Known commands:')
    print ('')
    print ('  dir  # set which dir the bitbox files are in')
    print ('  c    # choose current preset, 1-16')
    print ('  p    # play a clip for the current preset: X,Y')
    print ('  r    # rename clip, specify coords and new name (can include subdir')
    print ('  q    # quit')

  def handle_dir(self, text):
    """Parses out which directory the user specified and returns it.

    Returns None if not a valid dir
    """
    tokens = text.split(' ')
    if len(tokens) == 1:
      print ('current path: %s' % self._dir)
      return None

    path = text.split(' ', 1)[1]
    if not os.path.isdir(path):
      print ('bad path: %s' % path)
      return None
    return path

  def _preset_filename(self, preset_num):
    return os.path.join(self._dir, 'SE0000%02d.xml' % preset_num)

  def _format_clip_filename(self, filename):
    filename = filename.replace('\\','/')
    return os.path.join(self._dir, filename)

  def choose_preset(self, text):
    """Parses text and extracts preset value

    Returns None on invalid input
    """

    tokens = text.split(' ')
    preset_num = -1
    try:
      preset_num = int(tokens[1])
    except:
      print ('Expected number between 1 and 16 after l command')
      return None

    if preset_num < 1 or preset_num > 16:
      print ('Expected number between 1 and 16 after l command')
      return None

    return preset_num

  def list_preset(self, preset_num):
    """Lists clips in given preset"""
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(preset_num))
    clips = xmlfilter.clips()
    for tracknum in range(0, 4):
      for clipnum in range(0, 4):
        print ('\n%d,%d: %s' % (tracknum, clipnum, clips[tracknum][clipnum]))

  def _parse_coords(self, text):
    """Parses a comma-separated pair of ints and does valiation.

    Returns: a tuple of two ints, or None on error
    """
    def print_error():
      print ('Expected coordinates after play command, like: 0,0')

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

    return (track_num, clip_num)

  def _get_clip(self, preset_num, track_num, clip_num):
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(preset_num))
    clips = xmlfilter.clips()

    clip_filename = clips[track_num][clip_num]
    if not clip_filename:
      print ('No clip at that position')

    return clip_filename

  def play_clip(self, preset_num, text):
    """Parses text and plays the given clip"""
    def print_error():
      print ('Expected coordinates after play command, like: 0,0')

    tokens = text.split(' ', 1)
    if len(tokens) != 2:
      print_error()
      return

    coords = self._parse_coords(tokens[1])
    if coords is None:
      return
    track_num, clip_num = coords

    clip_filename = self._get_clip(preset_num, track_num, clip_num)
    if not clip_filename:
      return

    self._player.play(self._format_clip_filename(clip_filename))

  def _backup_preset(self, preset_num):
    """Make a copy of the preset file"""
    oldpath = os.path.join(self._dir, self._preset_filename(preset_num))
    newpath = oldpath.replace('.xml', '.bak')
    shutil.copy(oldpath, newpath)

  def _move_file(self, root, oldname, newname):
    oldpath = os.path.join(root, oldname.replace('\\','/'))
    if not os.path.isfile(oldpath):
      print ('Source file does not exist: %s' % oldpath)
      return False


    newpath = os.path.join(root, newname)
    if os.path.isfile(newpath):
      print ('Destination file already exists: %s' % newpath)
      return False

    if not os.path.isdir(os.path.dirname(newpath)):
      p = pathlib.Path(os.path.dirname(newpath))
      try:
        p.mkdir(parents=True)
      except Exception as e:
        print ('Error creating dir for %s: %s' % (newpath, e))
        return False

    shutil.move(oldpath, newpath)
    return True

  def rename_clip(self, preset_num, text):
    def print_error():
      print ('Expected coordinates and new filename, like: 0,0 foo/bar/baz.wav')

    tokens = text.split(' ', 2)
    if len(tokens) != 3:
      print_error()
      return

    coords = self._parse_coords(tokens[1])
    if coords is None:
      return
    track_num, clip_num = coords

    clip_filename = self._get_clip(preset_num, track_num, clip_num)
    if not clip_filename:
      return

    newname = tokens[2].strip()

    self._backup_preset(preset_num)
    preset_filename = self._preset_filename(preset_num)
    backup_filename = preset_filename.replace('.xml', '.bak')

    if not self._move_file(self._dir, clip_filename, newname):
      return

    parser = xml.sax.make_parser()
    with open(preset_filename, 'w') as out:
      renamer = bbxml.BBXMLRename(parser, out, track_num, clip_num, newname)
      renamer.parse(backup_filename)
