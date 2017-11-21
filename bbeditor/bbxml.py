""" bbxml.py
Process BitBox XML files, with different filters for different operations.
"""

import copy
import pathlib
import xml.sax
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

class BBXML(XMLFilterBase):
  """Base class for BitBox XML Processing.

  Loads filenames for each clip into memory for access.
  """
  def __init__(self, parser):
    """parser: a xml.sax.make_parser() object"""
    super().__init__(parser)
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = [['' for j in range(0,4)] for i in range(0,4)]

  def parse(self, source):
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = [['' for j in range(0,4)] for i in range(0,4)]
    super().parse(source)

  def clips(self):
    """Returns a copy of the list of clips (readonly)."""
    return copy.deepcopy(self._clips)

  def startElement(self, name, attrs):
    if name == 'track':
      self._cur_track += 1
    elif name == 'clip':
      self._cur_clip += 1
      if attrs['filename']:
        self._clips[self._cur_track][self._cur_clip] = attrs['filename']

  def endElement(self, name):
    if name == 'track':
      self._cur_clip = -1


class BBXMLRepoint(BBXML):
  """Repoints filenames in the XML.

  Silently converts paths to Windows-style path separators.

  Arguments:
    parser: the xml.sax.make_parser() object
    output: the output file object
    coords: a coordinate dictionary with int keys 'track' and 'clip'
    newname: the new name for the clip at those coordinates
  """

  def __init__(self, parser, output, coords, newname):
    super().__init__(parser)
    self._output = XMLGenerator(output)
    self._coords = coords
    # BitBox uses windows-style paths
    self._newname = pathlib.PureWindowsPath(newname) if newname != '' else ''

  def startElement(self, name, attrs):
    super().startElement(name, attrs)
    new_attrs = dict(attrs)
    if name == 'clip':
      if self._cur_track == self._coords['track'] and self._cur_clip == self._coords['clip']:
        new_attrs['file'] = "0"
        new_attrs['filename'] = str(self._newname)
    self._output.startElement(name, new_attrs)

  def endElement(self, name):
    super().endElement(name)
    self._output.endElement(name)

  def characters(self, content):
    self._output.characters(content)
