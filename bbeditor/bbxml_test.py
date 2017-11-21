import io
import unittest
import xml.sax


import bbxml


class PromptTest(unittest.TestCase):
  def _make_xmlio(self):
    return io.StringIO(r"""<document>
    <session>
        <track excl="1" out="4" level="0">
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="420" quant="4" loop="1" pitch="0" filename="130\09\slitekick01.wav" slize="1024" midimode="0">
                <slices>
                    <slice pos="0"></slice>
                    <slice pos="22016"></slice>
                    <slice pos="44032"></slice>
                    <slice pos="66560"></slice>
                </slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="400" quant="4" loop="1" pitch="0" filename="130\09\sbigkick01.wav" slize="1024" midimode="0">
                <slices>
                    <slice pos="0"></slice>
                    <slice pos="22016"></slice>
                    <slice pos="44032"></slice>
                    <slice pos="66304"></slice>
                </slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="2" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="1" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
        </track>
        <track excl="0" out="3" level="0">
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="0" quant="4" loop="1" pitch="0" filename="130\09\WUBWUB01.WAV" slize="1" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="12000" quant="4" loop="1" pitch="0" filename="130\09\MODHAT01.WAV" slize="4" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="2" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="1" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
        </track>
        <track excl="0" out="3" level="0">
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="0" quant="4" loop="1" pitch="0" filename="130\09\ZAP01.WAV" slize="1" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="0" quant="4" loop="1" pitch="0" filename="130\09\KLAX01.WAV" slize="1" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="0" quant="4" loop="1" pitch="0" filename="130\09\REVZAP01.WAV" slize="1" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="3" start="0" length="0" level="0" quant="4" loop="1" pitch="0" filename="130\09\SPARK01.WAV" slize="1" midimode="0">
                <slices></slices>
            </clip>
        </track>
        <track excl="0" out="3" level="0">
            <clip reverse="0" file="0" slicemode="0" trigtype="2" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="2" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="2" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
            <clip reverse="0" file="0" slicemode="0" trigtype="1" start="0" length="0" level="0" quant="0" loop="0" pitch="0" filename="" slize="0" midimode="0">
                <slices></slices>
            </clip>
        </track>
        <track excl="0" out="3" level="0">
            <altcell modamount="1000" modmode="scenetrig" moddest="0"></altcell>
            <altcell modamount="1000" modmode="scenetrig" moddest="0"></altcell>
            <altcell modamount="1000" modmode="scenetrig" moddest="0"></altcell>
            <altcell modamount="1000" modmode="scenetrig" moddest="0"></altcell>
        </track>
    </session>
</document>
""")
  def setUp(self):
    self._xml = self._make_xmlio()

  def test_read_xml(self):
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._xml)
    got = xmlfilter.clips()
    self.assertEqual([{'level': '420', 'length': '0', 'slicemode': '0',
                       'quant': '4', 'file': '0',
                       'slices': ['0', '22016', '44032', '66560'],
                       'midimode': '0', 'start': '0', 'trigtype': '3',
                       'loop': '1', 'pitch': '0', 'reverse': '0', 'slize': '1024',
                       'filename': '130\\09\\slitekick01.wav'},
                       {'level': '400', 'length': '0', 'slicemode': '0',
                        'quant': '4', 'file': '0',
                        'slices': ['0', '22016', '44032', '66304'],
                        'midimode': '0', 'start': '0', 'trigtype': '3',
                        'loop': '1', 'pitch': '0', 'reverse': '0',
                        'slize': '1024', 'filename': '130\\09\\sbigkick01.wav'},
                       {'level': 0, 'length': 0, 'slicemode': 0, 'quant': 0,
                        'file': 0, 'slices': [], 'midimode': 0, 'start': 0,
                        'trigtype': 0, 'loop': 0, 'pitch': 0, 'reverse': 0,
                        'slize': 0, 'filename': ''},
                       {'level': 0, 'length': 0, 'slicemode': 0, 'quant': 0,
                        'file': 0, 'slices': [], 'midimode': 0, 'start': 0,
                        'trigtype': 0, 'loop': 0, 'pitch': 0, 'reverse': 0,
                        'slize': 0, 'filename': ''}], got[0])

  def test_repoint_xml_windowspath(self):
    with io.StringIO() as out:
      parser = xml.sax.make_parser()
      coords = {'track': 0, 'clip': 0}
      newname = '130\\09\\slitenewname.wav'
      repointer = bbxml.BBXMLRepoint(parser, out, coords, newname)
      repointer.parse(self._xml)

      out.seek(0)
      parser2 = xml.sax.make_parser()
      xmlfilter = bbxml.BBXML(parser)
      xmlfilter.parse(out)
      got = xmlfilter.clips()

      self.assertEqual({'level': '420', 'length': '0', 'slicemode': '0',
                       'quant': '4', 'file': '0',
                       'slices': ['0', '22016', '44032', '66560'],
                       'midimode': '0', 'start': '0', 'trigtype': '3',
                       'loop': '1', 'pitch': '0', 'reverse': '0', 'slize': '1024',
                       'filename': '130\\09\\slitenewname.wav'}, got[0][0])

  def test_repoint_xml_unixpath(self):
    """Unix paths are converted to windows paths"""
    with io.StringIO() as out:
      parser = xml.sax.make_parser()
      coords = {'track': 0, 'clip': 1}
      newname = '130/09/unixslash.wav'
      repointer = bbxml.BBXMLRepoint(parser, out, coords, newname)
      repointer.parse(self._xml)

      out.seek(0)
      xmlfilter = bbxml.BBXML(parser)
      xmlfilter.parse(out)
      got = xmlfilter.clips()

      self.assertEqual('130\\09\\unixslash.wav', got[0][1]['filename'])

  def test_overwrite(self):
    """Test overwriting clip data from one to another, deleting slices"""
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._xml)
    clips = xmlfilter.clips()

    with io.StringIO() as out:
      coords = {'track': 0, 'clip': 0}
      newclip = clips[1][0]
      overwriter = bbxml.BBXMLOverwrite(parser, out, coords, newclip)
      xml2 = self._make_xmlio()
      overwriter.parse(xml2)

      out.seek(0)
      xmlfilter = bbxml.BBXML(parser)
      xmlfilter.parse(out)
      got = xmlfilter.clips()

      self.assertEqual(clips[1][0], got[0][0])

  def test_overwrite2(self):
    """Test overwriting clip data from one to another, creating slices"""
    parser = xml.sax.make_parser()
    xmlfilter = bbxml.BBXML(parser)
    xmlfilter.parse(self._xml)
    clips = xmlfilter.clips()

    with io.StringIO() as out:
      coords = {'track': 3, 'clip': 0}
      newclip = clips[0][0]
      overwriter = bbxml.BBXMLOverwrite(parser, out, coords, newclip)
      xml2 = self._make_xmlio()
      overwriter.parse(xml2)

      out.seek(0)
      xmlfilter = bbxml.BBXML(parser)
      xmlfilter.parse(out)
      got = xmlfilter.clips()

      self.assertEqual(clips[0][0], got[3][0])


if __name__ == "__main__":
  unittest.main()
