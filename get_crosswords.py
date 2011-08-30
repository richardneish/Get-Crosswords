#!/usr/bin/python
import mechanize
from lxml import etree
from StringIO import StringIO
import logging
import sys
from ConfigParser import ConfigParser
from os import path

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("get_crosswords")

log.debug("Get configuration from .rc file.")
config = ConfigParser({"directory" : "~/Documents/crosswords"})
config.read(path.expanduser("~/.get_crosswords.rc"))
email = config.get("Credentials", "email")
password = config.get("Credentials", "password")
output_dir = path.expanduser(config.get("Output", "directory"))

log.debug("Get the login page.")
br = mechanize.Browser()
response = br.open("http://puzzles.telegraph.co.uk/site/index.php")

log.debug("Pretty print the login page to clean up dodgy HTML.")
parser = etree.HTMLParser()
tree = etree.parse(StringIO(response.get_data()), parser)
response.set_data(etree.tostring(tree.getroot(),
                  pretty_print=True, method="html"))
br.set_response(response)

log.debug("Log in as user '" + email + "'.")
br.select_form(name="login")
br["loginDetails[email]"] = email
br["loginDetails[password]"] = password
response = br.submit()

log.debug("Parse the page and extract the puzzle links.")
tree = etree.parse(StringIO(response.get_data()), parser)
quick_title = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                         "'QUICK')]/text()")[0]
quick_link = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                        "'QUICK')]/following-sibling::a[1]/@href")[0]
log.info("Quick puzzle '" + quick_title + "' is at '" + quick_link + "'.")
cryptic_title = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                           "'CRYPTIC')]/text()")[0]
cryptic_link = tree.xpath("//div[@id='latest_games']//p[starts-with(text(), " +
                          "'CRYPTIC')]/following-sibling::a[1]/@href")[0]
log.info("Cryptic puzzle '" + cryptic_title + "' is at '" + cryptic_link + "'.")

log.debug("Write the puzzles out to local files.")
response = br.open(quick_link)
tree = etree.parse(StringIO(response.get_data()), parser)
quick = open(path.join(output_dir, quick_title + ".html"), "w")
quick.write(etree.tostring(tree.getroot(), pretty_print=True, method="xml"))
quick.close()
response = br.open(cryptic_link)
tree = etree.parse(StringIO(response.get_data()), parser)
cryptic = open(path.join(output_dir, cryptic_title + ".html"), "w")
cryptic.write(etree.tostring(tree.getroot(), pretty_print=True, method="xml"))
cryptic.close()

