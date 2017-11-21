"""mutations for audio files

* gain
* normalize
* trim to zero crossings?
* normalize a group of clips so they stay relatively the same
"""

import logging
import os.path
import shutil

import pydub
from pydub.playback import play
from pydub.utils import db_to_float, ratio_to_db

#l = logging.getLogger("pydub.converter")
#l.setLevel(logging.DEBUG)
#l.addHandler(logging.StreamHandler())

class Effector(object):
  def __init__(self, filename):
    self._filename = filename
    self._seg = pydub.AudioSegment.from_wav(self._filename)
    base, ext = os.path.splitext(self._filename)
    self._backupname = base + '.bak'

  def play(self):
    play(self._seg)

  def get_filename(self):
    return self._filename

  def _backup_clip(self):
    shutil.copy(self._filename, self._backupname)

  def _export(self):
    self._backup_clip()
    # pydub outputs 24bit as 32, and the files don't play in bitbox.  Instead drop to 16
    self._seg = self._seg.set_sample_width(2)
    self._seg.export(self._filename, format="wav")

  def normalize(self):
    self._seg = self._seg.normalize()
    self._export()

  def undo(self):
    if not os.path.isfile(self._backupname):
      print ('no backup to restore, sorry')
    shutil.copy(self._backupname, self._filename)

  def get_normalize_gain(self, headroom=0.1):
    # cribbed from pydub's code
    peak_sample_val = self._seg.max

    # if the max is 0, this audio segment is silent, and can't be normalized
    if peak_sample_val == 0:
      return 0

    target_peak = self._seg.max_possible_amplitude * db_to_float(-headroom)

    return ratio_to_db(target_peak / peak_sample_val)

  def apply_gain(self, boost):
    self._seg = self._seg.apply_gain(boost)
    self._export()

  def trim_to_zero_crossings(self):
    """Make samples loop-compatible with hopefully minimal affect on the length.

    Starts at the beginning and deletes samples until something ~0 is found.
    Does the same from the end.
    Reports how many samples were deleted
    """

    samples = self._seg.get_array_of_samples()
    oldlen = len(samples)
    # assuming stereo?
    trimsize = 0
    while trimsize < 1000:
      if abs(samples[0]) > 10 or abs(samples[1]) > 10:
        samples = samples[2:]
      trimsize += 1

    if trimsize == 1000:
      print ("%s: Didn't find a good zero crossing" % self._filename)
      return

    trimsize = 0
    while trimsize < 1000:
      if abs(samples[-1]) > 10 or abs(samples[-2]) > 10:
        samples = samples[:-2]
      trimsize += 1

    if trimsize == 1000:
      print ("%s: Didn't find a good zero crossing" % self._filename)
      return

    print ('%s Trimming %d samples' % (self._filename, oldlen - len(samples)))

    self._seg = self._seg._spawn(samples)
    self._export()

  def to_mono(self):
    # Still broken!
    self._seg = self._seg.apply_gain(0.5)
    self._seg = self._seg.set_channels(1)
    self._export()


def normalize_preset(filenames):
  """Normalizes all the clips in one preset equally.

  Goes through each file and gets the needed boost.  Takes the min of those
  and applies that to all of them
  """

  min_boost = -1
  effectors = [Effector(f) for f in filenames]
  for e in effectors:
    boost = e.get_normalize_gain()
    print ('%s: %d' % (e.get_filename(), boost))
    if min_boost == -1 or boost < min_boost:
      min_boost = boost

  for e in effectors:
    e.apply_gain(min_boost)
