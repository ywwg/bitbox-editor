""" bbxml.py
Eventually this will have to munge files and call osutil and whatnot.
not sure if I want two classes, one just for reading and another for reading and writing.
"""

import xml.sax
from xml.sax.saxutils import XMLFilterBase

class BBXML(XMLFilterBase):
  def __init__(self, input_xml, output_xml):
    super().__init__(input_xml)
    self._output_xml = output_xml
    self._cur_track = -1
    self._cur_clip = -1

    # List of clip filenames
    self._clips = []

  def parse(self, source):
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = []
    super().parse(source)

  def clips(self):
    return list(self._clips)

  def startElement(self, name, attrs):
    if name == 'track':
      self._cur_track += 1
    elif name == 'clip':
      self._cur_clip += 1
      if attrs['filename']:
        self._clips.append(attrs['filename'])

  def endElement(self, name):
    if name == 'track':
      self._cur_clip = -1

  def characters(self, content):
    pass
