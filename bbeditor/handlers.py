"""mostly stateless module for handling commands.

There is a stateful player, that's it.
"""
import os.path
import pathlib
import shutil
import xml.sax

import bbeditor.bbxml as bbxml
import bbeditor.playback as playback

class Handler(object):
  def __init__(self):
    self._player = playback.Player()

  def _preset_filename(self, root, preset_num):
    return os.path.join(root, 'SE0000%02d.xml' % preset_num)

  def _format_clip_filename(self, root, filename):
    filename = filename.replace('\\','/')
    return os.path.join(root, filename)

  def list_preset(self, root, preset_num, coords):
    """Lists clips in given preset"""
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(root, preset_num))
    clips = xmlfilter.clips()
    print ('')
    for tracknum in range(0, 4):
      for clipnum in range(0, 4):
        if tracknum == coords['track'] and clipnum == coords['clip']:
          print ('*', end='')
        else:
          print (' ', end='')
        print ('%d,%d: %s' % (tracknum, clipnum, clips[tracknum][clipnum]))

  def get_clip(self, root, preset_num, coords):
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(root, preset_num))
    clips = xmlfilter.clips()

    clip_filename = clips[coords['track']][coords['clip']]
    if not clip_filename:
      print ('No clip at that position')

    return clip_filename

  def play_clip(self, root, preset_num, coords):
    """Parses text and plays the given clip"""
    clip_filename = self.get_clip(root, preset_num, coords)
    if not clip_filename:
      return

    self._player.play(self._format_clip_filename(root, clip_filename))

  def _backup_preset(self, root, preset_num):
    """Make a copy of the preset file"""
    oldpath = os.path.join(root, self._preset_filename(root, preset_num))
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

  def rename_clip(self, root, preset_num, coords, newname):
    clip_filename = self.get_clip(root, preset_num, coords)
    if not clip_filename:
      return

    self._backup_preset(root, preset_num)

    preset_filename = self._preset_filename(root, preset_num)
    backup_filename = preset_filename.replace('.xml', '.bak')

    if not self._move_file(root, clip_filename, newname):
      return

    parser = xml.sax.make_parser()
    with open(preset_filename, 'w') as out:
      renamer = bbxml.BBXMLRename(parser, out, coords, newname)
      renamer.parse(backup_filename)
