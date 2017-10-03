#!/usr/bin/python3

import pathlib
import os.path

import bbeditor.prompt

if __name__ == "__main__":
  herstory_file = os.path.join(str(pathlib.Path.home()), '.bitboxeditor-history-file')

  prog = bbeditor.prompt.Prompt(herstory_file)
  running = True
  while running:
    running = prog.do_prompt()
