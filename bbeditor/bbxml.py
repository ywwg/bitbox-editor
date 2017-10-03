""" bbxml.py
Eventually this will have to munge files and call osutil and whatnot.
not sure if I want two classes, one just for reading and another for reading and writing.
"""

import copy
import xml.sax
from xml.sax.saxutils import XMLFilterBase

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
