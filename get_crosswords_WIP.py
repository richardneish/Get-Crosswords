#!/usr/bin/python
import argparse
from datetime import date, timedelta
from TelegraphCrossword import TelegraphCrossword

######## MAIN PROGRAM ######
if __name__ == "__main__":    
  parser = argparse.ArgumentParser(description='Convert crosswords to other formats')
  parser.add_argument('--input', \
      metavar='INPUT_TITLE', \
      help='Load a crossword and solution from local HTML files')
  args = parser.parse_args()

  tc = TelegraphCrossword()
  if (args.input == None):
    tc.login()

    yesterday = date.today() + timedelta(-1)
    print "Yesterday: %04d-%02d-%02d%%2000:00:00" % (yesterday.year, yesterday.month, yesterday.day)
    
    for type in ["quick", "cryptic"]:
        (title, crossword_tree, solution_tree) = tc.download(yesterday, type)
        tc.save(title, crossword_tree, solution_tree)
  else:
    title = args.input
    (crossword_tree, solution_tree) = tc.load(title)
  

