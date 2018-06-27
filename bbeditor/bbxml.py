""" bbxml.py
Process BitBox XML files, with different filters for different operations.
"""

import copy
import pathlib
import xml.sax
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

class BBXML(XMLFilterBase):
  """Base class for BitBox XML Processing.

  Loads clip data for each clip into memory for access.
  """

  TEMPLATE_CLIP = {
      'reverse': 0,
      'file': 0,
      'slicemode': 0,
      'trigtype': 0,
      'start': 0,
      'length': 0,
      'level': 0,
      'quant': 0,
      'loop': 0,
      'pitch': 0,
      'filename': '',
      'slize': 0,
      'midimode': 0,
      'slices': [],
    }

  def __init__(self, parser):
    """parser: a xml.sax.make_parser() object"""
    super().__init__(parser)
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = [[copy.deepcopy(self.TEMPLATE_CLIP) for j in range(0,4)] for i in range(0,4)]

  def parse(self, source):
    self._cur_track = -1
    self._cur_clip = -1
    self._clips = [[copy.deepcopy(self.TEMPLATE_CLIP) for j in range(0,4)] for i in range(0,4)]
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
        for k in dict(attrs):
          self._clips[self._cur_track][self._cur_clip][k] = attrs[k]
    elif name == 'slice':
      self._clips[self._cur_track][self._cur_clip]['slices'].append(attrs['pos'])

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


class BBXMLOverwrite(BBXML):
  """Overwrites clip metadata in the XML.

  Arguments:
    parser: the xml.sax.make_parser() object
    output: the output file object
    coords: a coordinate dictionary with int keys 'track' and 'clip'
    clipdata: a dictionary of clip data as returned by clips()
  """

  def __init__(self, parser, output, coords, clipdata):
    super().__init__(parser)
    self._output = XMLGenerator(output)
    self._coords = coords
    self._clipdata = clipdata
    self._in_clip = False

  def startElement(self, name, attrs):
    super().startElement(name, attrs)
    new_attrs = dict(attrs)
    if name == 'clip':
      self._in_clip = True
      if self._cur_track == self._coords['track'] and self._cur_clip == self._coords['clip']:
        for k in self._clipdata:
          if k == 'slices':
            continue
          new_attrs[k] = str(self._clipdata[k])
        self._output.startElement(name, new_attrs)
        self._output.characters('\n                ')
        self._output.startElement('slices', {})
        for sl in self._clipdata['slices']:
          self._output.characters('\n                    ')
          self._output.startElement('slice', {'pos': sl})
          self._output.endElement('slice')
        if self._clipdata['slices']:
          self._output.characters('\n                ')
        self._output.endElement('slices')
        return
    if name.startswith('slice'):
      if self._cur_track == self._coords['track'] and self._cur_clip == self._coords['clip']:
        return
    self._output.startElement(name, new_attrs)

  def endElement(self, name):
    super().endElement(name)
    # To make whitespace preservation work, we say we're done with a clip after
    # we see the close tag for the slices.
    if name == 'slices':
      self._in_clip = False
    if name.startswith('slice'):
      if self._cur_track == self._coords['track'] and self._cur_clip == self._coords['clip']:
        return
    self._output.endElement(name)

  def characters(self, content):
    if self._in_clip:
      if self._cur_track == self._coords['track'] and self._cur_clip == self._coords['clip']:
        return
    self._output.characters(content)
