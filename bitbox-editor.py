#!/usr/bin/python3


import bbeditor.prompt

if __name__ == "__main__":
  prog = bbeditor.prompt.Prompt()
  running = True
  while running:
    running = prog.do_prompt()
