"""mostly stateless module for handling commands.

There is a stateful player, that's it.
"""
import os.path
import pathlib
import shutil
import xml.sax

import bbeditor.bbxml as bbxml
import bbeditor.effects as effects
import bbeditor.playback as playback

class Handler(object):
  def __init__(self):
    self._player = playback.Player()

  def _preset_filename(self, root, preset_num):
    return os.path.join(root, 'SE0000%02d.xml' % preset_num)

  def _get_clips(self, root, preset_num):
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(root, preset_num))
    return xmlfilter.clips()

  def list_preset(self, root, preset_num, coords):
    """Lists clips in given preset"""
    clips = self._get_clips(root, preset_num)
    print ('')
    print ('Preset %d:' % preset_num)
    for tracknum in range(0, 4):
      for clipnum in range(0, 4):
        if tracknum == coords['track'] and clipnum == coords['clip']:
          print ('*', end='')
        else:
          print (' ', end='')
        print ('%d,%d: %s' % (tracknum, clipnum, clips[tracknum][clipnum]))

  def get_clip(self, root, preset_num, coords):
    """Gets the encoded clip name, which is a bad windows-style relative path.

    Use _format_clip_filename to get something useful
    """
    clips = self._get_clips(root, preset_num)
    clip_filename = clips[coords['track']][coords['clip']]
    return clip_filename

  def play_clip(self, root, preset_num, coords):
    """Parses text and plays the given clip"""
    clip_filename = self.get_clip(root, preset_num, coords)
    if not clip_filename:
      print ('No clip at that position')
      return

    self._player.play(self._format_clip_filename(root, clip_filename))

  def _backup_preset(self, root, preset_num):
    """Make a copy of the preset file"""
    oldpath = os.path.join(root, self._preset_filename(root, preset_num))
    newpath = oldpath.replace('.xml', '.bak')
    shutil.copy(oldpath, newpath)

  def _format_clip_filename(self, root, suffix):
    return os.path.join(root, suffix.replace('\\','/'))

  def _file_exists(self, root, suffix):
    path = self._format_clip_filename(root, suffix)
    return os.path.isfile(path)

  def _move_file(self, root, oldname, newname):
    if not self._file_exists(root, oldname):
      print ('Source file does not exist: %s' % oldname)
      return False

    newpath = self._format_clip_filename(root, newname)
    if self._file_exists(root, newpath):
      print ('Destination file already exists: %s' % newpath)
      return False

    if not os.path.isdir(os.path.dirname(newpath)):
      p = pathlib.Path(os.path.dirname(newpath))
      try:
        p.mkdir(parents=True)
      except Exception as e:
        print ('Error creating dir for %s: %s' % (newpath, e))
        return False

    oldpath = self._format_clip_filename(root, oldname)
    shutil.move(oldpath, newpath)
    return True

  def move_clip(self, root, preset_num, coords, newname):
    """Move file for a clip"""
    clip_filename = self.get_clip(root, preset_num, coords)
    if not clip_filename:
      print ('No clip at that position')
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

  def rename_clip(self, root, preset_num, coords, newname):
    """Just rename the file in the xml, don't move anything"""
    if newname:
      # Only check for path existence if not blank
      if not self._file_exists(root, newname):
        print ('New filename does not exist, rename failed: %s' % newname)
        return
    self._backup_preset(root, preset_num)

    preset_filename = self._preset_filename(root, preset_num)
    backup_filename = preset_filename.replace('.xml', '.bak')

    parser = xml.sax.make_parser()
    with open(preset_filename, 'w') as out:
      renamer = bbxml.BBXMLRename(parser, out, coords, newname)
      renamer.parse(backup_filename)

  def normalize_clip(self, root, preset_num, coords):
    clipname = self.get_clip(root, preset_num, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.normalize()

  def normalize_preset(self, root, preset_num):
    clips = self._get_clips(root, preset_num)
    files = [self._format_clip_filename(root, c) for t in clips for c in t if c != '']
    effects.normalize_preset(files)

  def trim_clip(self, root, preset_num, coords):
    clipname = self.get_clip(root, preset_num, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.trim_to_zero_crossings()

  def trim_all(self, root, preset_num):
    clips = self._get_clips(root, preset_num)
    files = [self._format_clip_filename(root, c) for t in clips for c in t if c != '']
    for f in files:
      effector = effects.Effector(f)
      effector.trim_to_zero_crossings()

  def undo_clip(self, root, preset_num, coords):
    clipname = self.get_clip(root, preset_num, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.undo()
