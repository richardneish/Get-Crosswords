#!/usr/bin/python
import mechanize
from lxml import etree
from StringIO import StringIO
import logging
import sys
from ConfigParser import ConfigParser
from os import path

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
    grid = []
    rows = tree.xpath("//table[2]//tr[2]//table//tr")
    gridheight = len(rows)
    for row in rows:
        images = row.xpath(".//img/@src")
        gridwidth = len(images)
        for image in :
            try:
                cell = re.match(r'^/_admin/printing/images/(.*\D)\d?\.gif$', image),group(1)
            except:
                log.error('Could not parse image src ' + image)
                cell = 'black_cell'
            if cell == 'white_cell':
                grid.append(' ')
            else if cell == 'black_cell':
                grid.append('.')
            else if num_match = re.match('^(\d+)_number$'):
                grid.append(num_match.group(1))
    return tree

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

