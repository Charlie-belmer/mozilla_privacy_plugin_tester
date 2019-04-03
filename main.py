import argparse
from plugin_ingestor import ingest_plugins
from db import get_plugins_to_test, pull_report
from plugin_tester import test_plugin
import random
import time
import json
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description="Find and test Firefox plugins for data privacy")
parser.add_argument("-c", "--crawl", action='store_true', help="Crawl Mozilla plugin repo for all plugins")
parser.add_argument("-i", "--ingest", action='store_true', help="Ingest any plugins in found via crawling into the database")
parser.add_argument("-t", "--test", action='store_true', help="Test all plugins whose test results are out of date")
parser.add_argument("-r", "--report", action='store_true', help="Generate a report in json of all results")

args = parser.parse_args()
args = vars(args)

min_delay = 5
max_delay = 20

def ingest():
    ingest_plugins()

def test():
    plugins = get_plugins_to_test()
    average_delay = (min_delay + max_delay / 2)
    completed = 0
    for plugin in plugins:
        print("Testing plugin " + plugin["name"] + "...")
        test_plugin(plugin["name"], plugin["url"], plugin["icon_url"], plugin["id"])

        # Random delay to limit liklihood of getting disconnects from firefox store
        delay = random.randint(5, 20) 
        completed += 1
        time_left = ((min_delay + max_delay / 2) + 15 ) / 60 * (len(plugins) - completed)
        print("--------------------------------------------------------------------")
        print("- Sleeping for " + str(delay) + " seconds (to limit abuse detection)")
        print("- Tested " + str(completed) + " plugins out of " + str(len(plugins)))
        print("- Approximate testing time remaining: " + str(time_left) + " minutes.")
        print("--------------------------------------------------------------------")
        time.sleep(delay)

def crawl():
    print("Crawl not yet implemented.")
    print("Use the manual invocation:")
    print("scrapy crawl privacy_monitor -o plugins.json")


def sanitize_html(value):
    VALID_TAGS = ['table', 'em', 'p', 'tr', 'th', 'td', 'br']
    soup = BeautifulSoup(value)

    for tag in soup.findAll(True):
        if tag.name not in VALID_TAGS:
            tag.hidden = True

    return soup.renderContents()

def report():
    outfile = "report.json"
    data = pull_report()
    for row in data:
        row['requests'] = row['requests'].replace('\r\n', "<br />")
        row['requests'] = str(sanitize_html(row['requests']), 'UTF8')
    with open(outfile, 'w') as f:
        f.write(json.dumps(data))

if __name__ == "__main__":
    if args["crawl"]:
        crawl()
    if args["ingest"]:
        ingest()
    if args["test"]:
        test()
    if args["report"]:
        report()