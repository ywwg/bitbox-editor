""" bbxml.py
Eventually this will have to munge files and call osutil and whatnot.
not sure if I want two classes, one just for reading and another for reading and writing.
"""

import copy
import pathlib
import xml.sax
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

class BBXML(XMLFilterBase):
  def __init__(self, input_xml):
    super().__init__(input_xml)
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = [['' for j in range(0,4)] for i in range(0,4)]

  def parse(self, source):
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = [['' for j in range(0,4)] for i in range(0,4)]
    super().parse(source)

  def clips(self):
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


class BBXMLRename(BBXML):
  def __init__(self, input_xml, output, coords, newname):
    super().__init__(input_xml)
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
