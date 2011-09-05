#!/usr/bin/python
import mechanize
from lxml import etree
from StringIO import StringIO
import logging
import sys
from ConfigParser import ConfigParser
from os import path

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
    #for row in tree.xpath("//table[2]//tr[2]//table//tr"):
	    
    return tree

def load_file(title):
    """Load a previously saved XHTML file, and build the parse tree """
    file = open(path.join(output_dir, title + ".html"), "r")
    tree = etree.parse(file.read(), parser)
    file.close()
    return tree

def save_file(title, tree):
    """Save the parse tree as XHTML """
    file = open(path.join(output_dir, title + ".html"), "w")
    file.write(etree.tostring(tree.getroot(), pretty_print=True, method="xml"))
    file.close()

def download_crossword(tree, type):
    title = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                       "'" + type + "')]/text()")[0]
    link = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                      "'" + type + "')]/following-sibling::a[1]/@href")[0]
    log.info("Downloading puzzle '" + title + "' from '" + link + "'.")
    response = br.open(link)
    crossword_tree = etree.parse(StringIO(response.get_data()), parser)
    return (title, crossword_tree)


######## MAIN PROGRAM ######
if __name__ == "__main__":
    """Configure logging """
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("get_crosswords")
    
    log.debug("Get configuration from .rc file.")
    config = ConfigParser({"directory" : "~/Documents/crosswords"})
    config.read(path.expanduser("~/.get_crosswords.rc"))
    email = config.get("Credentials", "email")
    password = config.get("Credentials", "password")
    output_dir = path.expanduser(config.get("Output", "directory"))
    
    br = mechanize.Browser()
    parser = etree.HTMLParser()
    response = login()
    log.debug("Parse the page and extract the puzzle links.")
    tree = etree.parse(StringIO(response.get_data()), parser)
    
    log.debug("Download the puzzles and reparse into the local form.")
    for type in ["QUICK", "CRYPTIC"]:
        (title, crossword_tree) = download_crossword(tree)
        local_format = convert_crossword(crossword_tree)
        save_file(title, local_format)

