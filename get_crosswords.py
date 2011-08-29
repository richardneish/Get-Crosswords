#!/usr/bin/python
import mechanize
from lxml import etree
from StringIO import StringIO
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("get_crosswords")

log.debug("Get configuration from .rc file.")
email = "username"
password = "password"

log.debug("Get the login page.")
br = mechanize.Browser()
response = br.open("http://puzzles.telegraph.co.uk/site/index.php")

log.debug("Pretty print the login page to clean up dodgy HTML.")
parser = etree.HTMLParser()
tree = etree.parse(StringIO(response.get_data()), parser)
response.set_data(etree.tostring(tree.getroot(),
                  pretty_print=True, method="html"))
br.set_response(response)

log.debug("Set the login name and password and submit the login form.")
br.select_form(name="login")
br["loginDetails[email]"] = email
br["loginDetails[password]"] = password
response = br.submit()

log.debug("Parse the page and extract the puzzle links.")
tree = etree.parse(StringIO(response.get_data()), parser)
tree.xpath("//div[@id='latest_games']")
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
quick = open(quick_title + ".html", "w")
quick.write(response.get_data())
quick.close()
response = br.open(cryptic_link)
cryptic = open(cryptic_title + ".html", "w")
cryptic.write(response.get_data())
cryptic.close()

