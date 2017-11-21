import os
import unittest
import tempfile

import prompt


class PromptTest(unittest.TestCase):
  def setUp(self):
    self._t = tempfile.NamedTemporaryFile()
    self._p = prompt.Prompt(self._t.name)
    self._p._root = '/'

  def test_parse_coords(self):
    self.assertEqual({'track': 0, 'clip': 0}, self._p._parse_coords('0,0'))
    self.assertEqual({'track': 2, 'clip': 3}, self._p._parse_coords('2,3'))
    self.assertEqual({'track': 1, 'clip': 2}, self._p._parse_coords(' 1 , 2   '))
    self.assertIsNone(self._p._parse_coords('0,'))
    self.assertIsNone(self._p._parse_coords('urmam'))
    self.assertIsNone(self._p._parse_coords('-1,3'))
    self.assertIsNone(self._p._parse_coords('0,4'))
    self.assertIsNone(self._p._parse_coords('x,y'))
    self.assertIsNone(self._p._parse_coords('0,2,1'))
    self.assertIsNone(self._p._parse_coords('0.1'))

  def test_parse_command(self):
    self.assertEqual({'command': 'p', 'coords': [], 'args': []},
                     self._p.parse_command('p'))
    self.assertEqual({'command': 'p', 'coords': [], 'args': []},
                     self._p.parse_command('p '))
    self.assertEqual({'command': 'play', 'coords': [], 'args': []},
                     self._p.parse_command('play'))
    self.assertEqual({'command': 'p', 'coords': [{'clip': 1, 'track': 2}], 'args': []},
                     self._p.parse_command('p 2,1'))
    self.assertEqual({'command': 'f', 'coords': [], 'args': ['foo/bar/baz']},
                     self._p.parse_command('f foo/bar/baz'))
    self.assertEqual({'command': 'f', 'coords': [{'clip': 2, 'track': 2}], 'args': ['foo/bar/baz with space.txt']},
                     self._p.parse_command('f 2,2 "foo/bar/baz with space.txt"'))
    self.assertEqual({'command': 's', 'coords': [
                       {'clip': 1, 'track': 2},
                       {'clip': 2, 'track': 3}
                     ], 'args': []},
                     self._p.parse_command('s 2,1   3,2'))

  def test_handle_dir(self):
    d = tempfile.mkdtemp()
    command = {
      'command': 'd',
      'coords': [],
      'args': ['/not/a/path'],
    }

    self.assertIsNone(self._p.handle_dir(command))

    command['args'][0] = d
    self.assertEqual(d, self._p.handle_dir(command))

    command['args'].append('oops')
    self.assertIsNone(self._p.handle_dir(command))

    command['args'] = []
    self.assertIsNone(self._p.handle_dir(command))

    os.rmdir(d)

  def test_choose_preset(self):
    with tempfile.NamedTemporaryFile(suffix='.xml') as t:
      preset_name = t.name.rstrip('.xml')
      command = {
        'command': 'c',
        'coords': [],
        'args': [preset_name],
      }
      self.assertEqual(preset_name, self._p.choose_preset(command))

      command['args'][0] = "nope"
      self.assertIsNone(self._p.choose_preset(command))

      command['args'] = []
      self.assertIsNone(self._p.choose_preset(command))


if __name__ == "__main__":
  unittest.main()
