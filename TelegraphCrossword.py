#!/usr/bin/python
import mechanize
from lxml import etree
from StringIO import StringIO
import logging
import sys
from ConfigParser import ConfigParser
from os import path
import string
import re
import json

class TelegraphCrossword:
  """Class encapsulating methods to download and parse Telegraph crosswords"""
  
  def __init__(self):
    """Configure logging """
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    self.log = logging.getLogger("get_crosswords")

    # TODO: allow user to pass in path to config file.
    self.log.debug("Get configuration from .rc file.")
    config = ConfigParser()
    config.read(path.expanduser("~/.get_crosswords.rc"))
    self.email = config.get("Credentials", "email")
    self.password = config.get("Credentials", "password")
    self.output_dir = path.expanduser(config.get("Output", "directory"))
    self.parser = etree.HTMLParser()
    self.br = mechanize.Browser()

  def login(self):
    self.log.debug("Get the login page.")
    response = self.br.open("http://puzzles.telegraph.co.uk/site/index.php")
    self.log.debug("Pretty print the login page to clean up dodgy HTML.")
    tree = etree.parse(StringIO(response.get_data()), self.parser)
    response.set_data(etree.tostring(tree.getroot(),
                      pretty_print=True, method="html"))
    self.br.set_response(response)

    self.log.debug("Log in as user '" + self.email + "'.")
    self.br.select_form(name="login")
    self.br["loginDetails[email]"] = self.email
    self.br["loginDetails[password]"] = self.password
    response = self.br.submit()
    return response

  def extract_grid(tree):
      """
         Extract the crossword grid and grid numbers from HTML.
         Returns the tuple (grid, gridnums).
      """
      grid = []
      gridnums = []
      rows = tree.xpath("//table[2]//tr[2]//table//tr")
      gridheight = len(rows)
      gridwidth = None
      for row in rows:
          images = row.xpath(".//img/@src")
          if gridwidth == None:
              gridwidth = len(images)
          for image in images:
              try:
                  cell = re.match(r'^/_admin/printing/images/(.*\D)\d*\.gif$', \
                                  image).group(1)
              except:
                  self.log.error('Could not parse image src [' + image + ']')
                  cell = 'black_cell'
              gridnum = 0
              if cell == 'white_cell':
                  grid.append(' ')
              elif cell == 'black_cell':
                  grid.append('.')
              else:
                  num_match = re.match(r'^(\d+)_number$', cell)
                  if num_match != None:
                      gridnum = num_match.group(1)
                      grid.append(' ')
              gridnums.append(gridnum)
      return gridheight, gridwidth, grid, gridnums

  def extract_clues(clues_in):
      """ Extract the crossword clues from HTML """
      clues_out = []
      for clue in clues_in:
          clue_split = clue.xpath('.//text()')
          if len(clue_split) == 2:
              (clue_num, clue_text) = clue_split
              clues_out.append(clue_num + '. ' + clue_text)
      return clues_out

  def build_json(title, tree):
      """
         Convert HTML to JSON format defined at 
         http://www.xwordinfo.com/JSON/
      """
      j = {}
      j['title'] = title
      j['size'] = {}
      (j['size']['rows'], j['size']['cols'], j['grid'], j['gridnums']) = \
          extract_grid(tree)
      j['clues'] = {}
      j['clues']['across'] = extract_clues(tree.xpath('//table[3]//td[2]//tr'))
      j['clues']['down'] = extract_clues(tree.xpath('//table[3]//td[4]//tr'))
      return json.dumps(j)

  def load(self, title):
      """Load a previously saved XHTML file, and build the parse tree """
      filename = path.join(self.output_dir, title + ".html")
      file = open(filename, "r")
      crossword_tree = etree.parse(file, self.parser)
      file.close()
      filename = path.join(self.output_dir, title + "_solution.html")
      if path.exists(filename):
        file = open(filename, "r")
        solution_tree = etree.parse(file, self.parser)
        file.close()
      else:
        solution_tree = None
      return (crossword_tree, solution_tree)

  def save(self, title, crossword_tree, solution_tree):
      """Save the parse tree as XHTML """
      filename = path.join(self.output_dir, title + ".html")
      file = open(filename, "w")
      file.write(etree.tostring(crossword_tree.getroot(), pretty_print=True, method="xml"))
      file.close()
      self.log.info("Saved '" + filename + "'")
      if solution_tree != None:
        filename = path.join(self.output_dir, title + "_solution.html")
        file = open(filename, "w")
        file.write(etree.tostring(solution_tree.getroot(), pretty_print=True, method="xml"))
        file.close()
        self.log.info("Saved '" + filename + "'")

  def download(self, date, type):
      # Search for ${date} and follow the link to get crossword and solution.
      url = "http://puzzles.telegraph.co.uk/site/view_puzzle.php?action=next&puzzleDate=%04d-%02d-%02d%%2000:00:00&puzzleType=%s&type=" \
            % (date.year, date.month, date.day, type)
      self.log.debug('Fetching search form')
      self.br.open('http://puzzles.telegraph.co.uk/site/crossword_puzzles');
      self.br.select_form(name = 'small_component_search');
      self.br.form['dayDate'] = date.day;
      self.br.form['monthDate'] = date.month;
      self.br.form['yearDate'] = date.year;
      self.log.debug('Searching for %s puzzle for %d-%d-%d', type, date.year, date.month, date.day);
      response = self.br.submit();
      tree = etree.parse(StringIO(response.get_data()), self.parser)
      nodes = tree.xpath(r'//div[@class="game_name_bar"]/p[1]//text()')
      title = nodes[0] + nodes[1]
      nodes = tree.xpath(r'//div[@class="game_details"]//a/@href')
      puzzle_link = None
      solution_link = None
      for link in nodes:
        self.log.debug('Examining link [%s]' % link)
        if re.match(r'^./print_crossword\?id=\d+$', link):
          self.log.debug('Found puzzle link [%s]' % link)
          puzzle_link = link
        if re.match(r'print_crossword.php\?id=\d+&action=solution', link):
          solution_link = link
      if puzzle_link != None:
        self.log.info("Downloading puzzle '" + title + "' from '" + puzzle_link + "'.")
        response = self.br.open(puzzle_link)
        crossword_tree = etree.parse(StringIO(response.get_data()), self.parser)
      else:
        self.log.error("Crossword link not found in response!" + response.get_data())
        crossword_tree = None
      if solution_link != None:
        self.log.info("Downloading solution '" + title + "' from '" + solution_link + "'.")
        response = self.br.open(solution_link)
        solution_tree = etree.parse(StringIO(response.get_data()), self.parser)
      else:
        self.log.info("Solution link not found in response.")
        solution_tree = None
      return (title, crossword_tree, solution_tree)

