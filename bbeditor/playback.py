""" playback.py
plays wav files, one at a time.  One will interrupt the previous
"""

import simpleaudio

class Player(object):
  def __init__(self):
    self._play_obj = None

  def play(self, filename):
    """Plays the given filename.

    If something is already playing, stop it first.

    Throws:
      FileNotFoundError if file not found.
      ValueError if the file is unsupported.
      _simpleaudio.SimpleaudioError for weird hardware/coding issues.
    """
    if self._play_obj is not None:
      self._play_obj.stop()

    wave_obj = simpleaudio.WaveObject.from_wave_file(filename)
    self._play_obj = wave_obj.play()

  def stop(self):
    """Stops currently playing file, if any.  No effect if not playing."""
    if self._play_obj is not None:
      self._play_obj.stop()
      self._play_obj = None
