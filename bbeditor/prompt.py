"""prompt.py
Like, handle all the possible commands and stuff
"""
import os.path
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

  def do_prompt(self):
    """Returns false if asked to quit."""

    text = prompt('(? for help) > ', history=self._herstory)

    if text == '?':
      self.help()
      return True
    elif text == 'q':
      return False
    elif text.startswith('dir'):
      self.handle_dir(text)
      return True

    if not self._dir:
      print ("Please set 'dir foo/bar' for bitbox directory")
      return True

    if text.startswith('l'):
      self.list_presets(text)
    elif text.startswith('p'):
      self.play_clip(text)

    return True

  def help(self):
    print ('Known commands:')
    print ('')
    print ('  l # list info for a preset')

  def handle_dir(self, text):
    tokens = text.split(' ')
    if len(tokens) == 1:
      print ('current path: %s' % self._dir)
      return

    path = text.split(' ', 1)[1]
    if not os.path.isdir(path):
      print ('bad path: %s' % path)
      return
    self._dir = path

  def _preset_filename(self, preset_num):
    return os.path.join(self._dir, 'SE0000%02d.xml' % preset_num)

  def _format_clip_filename(self, filename):
    filename = filename.replace('\\','/')
    return os.path.join(self._dir, filename)

  def list_presets(self, text):
    tokens = text.split(' ')
    preset_num = -1
    try:
      preset_num = int(tokens[1])
    except:
      print ('Expected number between 1 and 16 after l command')
      return

    if preset_num < 1 or preset_num > 16:
      print ('Expected number between 1 and 16 after l command')
      return

    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(preset_num))
    clips = xmlfilter.clips()
    for tracknum in range(0, 4):
      for clipnum in range(0, 4):
        print ('%d,%d: %s' % (tracknum, clipnum, clips[tracknum][clipnum]))

  def play_clip(self, text):
    tokens = text.split(' ', 1)

    def print_error():
      print ('Expected preset number and coordinates after play command, like: 1,0,0')

    if len(tokens) != 2:
      print_error()
      return
    coords = tokens[1].split(',')
    if len(coords) != 3:
      print_error()
      return

    preset_num = int(coords[0])
    if preset_num < 1 or preset_num > 16:
      print_error()
      return
    track_num = int(coords[1])
    if track_num < 0 or track_num > 3:
      print_error()
      return
    clip_num = int(coords[2])
    if clip_num < 0 or clip_num > 3:
      print_error()
      return
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(preset_num))
    clips = xmlfilter.clips()

    clip_filename = clips[track_num][clip_num]
    if not clip_filename:
      print ('No clip at that position')
      return

    self._player.play(self._format_clip_filename(clip_filename))
