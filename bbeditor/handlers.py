"""mostly stateless module for handling commands.

There is a stateful player, that's it.
"""
import os.path
import pathlib
import shutil
import xml.sax

import bbeditor.bbxml as bbxml
import bbeditor.effects as effects

class Error(Exception):
  """Base class for exceptions in this module."""
  pass

class NoClipError(Error):
  pass

class FileNotFound(Error):
  def __init__(self, filename):
    self.filename = filename

class FileAlreadyExists(Error):
  def __init__(self, filename):
    self.filename = filename

class MkdirError(Error):
  def __init__(self, path, err):
    self.path = path
    self.err = err

class FileMoveError(Error):
  def __init__(self, err):
    self.err = err

class InvalidCoordinates(Error):
  pass

class Handler(object):
  def __init__(self):
    pass

  def _preset_filename(self, root, preset_name):
    return os.path.join(root, '%s.xml' % preset_name)

  def _get_clips(self, root, preset_name):
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._preset_filename(root, preset_name))
    return xmlfilter.clips()

  def get_clips_filenames(self, root, preset_name):
    clips = self._get_clips(root, preset_name)
    files = [['' for j in range(0,4)] for i in range(0,4)]
    for i in range(0, 4):
      for j in range(0, 4):
        files[i][j] = clips[i][j]['filename']
    return files

  def get_clip(self, root, preset_name, coords):
    """Gets the encoded clip name, which is a bad windows-style relative path.

    Use _format_clip_filename to get something useful
    """
    clips = self.get_clips_filenames(root, preset_name)
    clip_filename = clips[coords['track']][coords['clip']]
    return clip_filename

  def play_clip(self, root, preset_name, coords):
    """Parses text and plays the given clip

    Raises:
      NoClipError
      FileNotFound
    """
    clipname = self.get_clip(root, preset_name, coords)
    if not clipname:
      raise NoClipError

    filename = self._format_clip_filename(root, clipname)
    if not os.path.isfile(filename):
      raise FileNotFound(filename)

    effector = effects.Effector(filename)
    effector.play()

  def _backup_preset(self, root, preset_name):
    """Make a copy of the preset file"""
    oldpath = os.path.join(root, self._preset_filename(root, preset_name))
    newpath = os.path.splitext(oldpath)[0] + '.bak'
    shutil.copy(oldpath, newpath)

  def _format_clip_filename(self, root, suffix):
    return os.path.join(root, suffix.replace('\\','/'))

  def _file_exists(self, root, suffix):
    path = self._format_clip_filename(root, suffix)
    return os.path.isfile(path)

  def _move_file(self, root, oldname, newname):
    """Moves a file, creating parent directories if necessary.

    Will not overwrite existing files.

    Raises:
      FileNotFound
      FileAlreadyExists
      MkdirError
      FileMoveError
    """
    if not self._file_exists(root, oldname):
      raise FileNotFound(oldname)

    newpath = self._format_clip_filename(root, newname)
    if self._file_exists(root, newpath):
      raise FileAlreadyExists(newpath)

    if not os.path.isdir(os.path.dirname(newpath)):
      p = pathlib.Path(os.path.dirname(newpath))
      try:
        p.mkdir(parents=True)
      except Exception as e:
        raise MkdirError(newpath, e)

    oldpath = self._format_clip_filename(root, oldname)
    try:
      shutil.move(oldpath, newpath)
    except Exception as e:
      raise FileMoveError(e)
    return True

  def move_clip(self, root, preset_name, coords, newname):
    """Move file for a clip on disk and update XML to match.

    Raises:
      NoClipError
      Everything that _move_file raises
    """
    clip_filename = self.get_clip(root, preset_name, coords)
    if not clip_filename:
      raise NoClipError

    self._backup_preset(root, preset_name)

    preset_filename = self._preset_filename(root, preset_name)
    backup_filename = os.path.splitext(preset_filename)[0] + '.bak'

    self._move_file(root, clip_filename, newname)

    parser = xml.sax.make_parser()
    with open(preset_filename, 'w') as out:
      repointer = bbxml.BBXMLRepoint(parser, out, coords, newname)
      repointer.parse(backup_filename)

  def move_preset(self, root, preset_name, newname):
    preset_filename = self._preset_filename(root, preset_name)
    new_filename = self._preset_filename(root, newname)
    self._move_file(root, preset_filename, new_filename)

  def repoint_clip(self, root, preset_name, coords, newname):
    """Just repoint the file in the xml, don't move anything.

    Doesn't check for old filename in case it was wrong (case problem)

    Raises:
      FileNotFound
    """
    if newname:
      # Only check for path existence if not blank
      if not self._file_exists(root, newname):
        raise FileNotFound(newname)
    self._backup_preset(root, preset_name)

    preset_filename = self._preset_filename(root, preset_name)
    backup_filename = os.path.splitext(preset_filename)[0] + '.bak'

    parser = xml.sax.make_parser()
    with open(preset_filename, 'w') as out:
      repointer = bbxml.BBXMLRepoint(parser, out, coords, newname)
      repointer.parse(backup_filename)

  def swap_clips(self, root, preset_name, this_coords, that_coords):
    clips = self._get_clips(root, preset_name)
    self._backup_preset(root, preset_name)
    preset_filename = self._preset_filename(root, preset_name)
    backup_filename = os.path.splitext(preset_filename)[0] + '.bak'
    inter_filename = os.path.splitext(preset_filename)[0] + '.inter'

    parser = xml.sax.make_parser()
    with open(inter_filename, 'w') as out:
      overwriter = bbxml.BBXMLOverwrite(
          parser, out, this_coords,
          clips[that_coords['track']][that_coords['clip']])
      overwriter.parse(backup_filename)

    with open(preset_filename, 'w') as out:
      overwriter = bbxml.BBXMLOverwrite(
          parser, out, that_coords,
          clips[this_coords['track']][this_coords['clip']])
      overwriter.parse(inter_filename)

    os.remove(inter_filename)

  def normalize_clip(self, root, preset_name, coords):
    clipname = self.get_clip(root, preset_name, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.normalize()

  def normalize_preset(self, root, preset_name):
    clips = self.get_clips_filenames(root, preset_name)
    files = [self._format_clip_filename(root, c) for t in clips for c in t if c != '']
    effects.normalize_preset(files)

  def trim_clip(self, root, preset_name, coords):
    clipname = self.get_clip(root, preset_name, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.trim_to_zero_crossings()

  def trim_all(self, root, preset_name):
    clips = self.get_clips_filenames(root, preset_name)
    files = [self._format_clip_filename(root, c) for t in clips for c in t if c != '']
    for f in files:
      effector = effects.Effector(f)
      effector.trim_to_zero_crossings()

  def clip_to_mono(self, root, preset_name, coords):
    clipname = self.get_clip(root, preset_name, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.to_mono()

  def undo_clip(self, root, preset_name, coords):
    clipname = self.get_clip(root, preset_name, coords)
    if clipname is None:
      return
    effector = effects.Effector(self._format_clip_filename(root, clipname))
    effector.undo()
