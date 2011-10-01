#!/usr/bin/python
import mechanize
from lxml import etree
from StringIO import StringIO
import logging
import sys
from ConfigParser import ConfigParser
from os import path
import re
import json

""" Globals """

def login():
    log.debug("Get the login page.")
    response = br.open("http://puzzles.telegraph.co.uk/site/index.php")
    log.debug("Pretty print the login page to clean up dodgy HTML.")
    tree = etree.parse(StringIO(response.get_data()), parser)
    response.set_data(etree.tostring(tree.getroot(),
                      pretty_print=True, method="html"))
    br.set_response(response)

    log.debug("Log in as user '" + email + "'.")
    br.select_form(name="login")
    br["loginDetails[email]"] = email
    br["loginDetails[password]"] = password
    response = br.submit()
    return response

def convert_crossword(tree):
    """
       Convert the Telegraph crossword HTML into a form suitable for offline
       solving.
       Input: An lxml etree object containing the Telegraph format HTML.
       Output: An lxml etree object containing the local form.
    """
    file = open(path.join(output_dir, title + ".html"), "r")
    tree = etree.parse(file, parser)
    file.close()
    template_tree = load_file('template')
    
    return tree

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
                log.error('Could not parse image src [' + image + ']')
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

def load_file(title):
    """Load a previously saved XHTML file, and build the parse tree """
    file = open(path.join(output_dir, title + ".html"), "r")
    tree = etree.parse(file, parser)
    file.close()
    return tree

def save_file(title, tree):
    """Save the parse tree as XHTML """
    filename = path.join(output_dir, title + ".html")
    file = open(filename, "w")
    file.write(etree.tostring(tree.getroot(), pretty_print=True, method="xml"))
    file.close()
    log.info("Saved '" + filename + "'")

def download_crossword(tree, type):
    title = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                       "'" + type + "')]/text()")[0]
    link = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                      "'" + type + "')]/following-sibling::a[1]/@href")[0]
    log.info("Downloading puzzle '" + title + "' from '" + link + "'.")
    response = br.open(link)
    crossword_tree = etree.parse(StringIO(response.get_data()), parser)
    return (title, crossword_tree)

######## MODULE INITIALIZATION ######
"""Configure logging """
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("get_crosswords")

log.debug("Get configuration from .rc file.")
config = ConfigParser({"directory" : "~/Documents/crosswords"})
config.read(path.expanduser("~/.get_crosswords.rc"))
email = config.get("Credentials", "email")
password = config.get("Credentials", "password")
output_dir = path.expanduser(config.get("Output", "directory"))
parser = etree.HTMLParser()
br = mechanize.Browser()

######## MAIN PROGRAM ######
if __name__ == "__main__":    
    response = login()
    log.debug("Parse the page and extract the puzzle links.")
    tree = etree.parse(StringIO(response.get_data()), parser)
    
    log.debug("Download the puzzles and reparse into the local form.")
    for type in ["QUICK", "CRYPTIC"]:
        (title, crossword_tree) = download_crossword(tree, type)
        save_file(title, crossword_tree)
        local_format = convert_crossword(crossword_tree)
        save_file(title + " (converted)", local_format)

