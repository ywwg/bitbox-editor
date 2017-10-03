#!/usr/bin/python3

import os.path

import bbeditor.prompt

if __name__ == "__main__":
  home = ""
  try:
    import pathlib
    home = str(pathlib.Path.home())
  except:
    from os.path import expanduser
    home = expanduser("~")
  herstory_file = os.path.join(home, '.bitboxeditor-history-file')

  prog = bbeditor.prompt.Prompt(herstory_file)
  running = True
  while running:
    running = prog.do_prompt()
