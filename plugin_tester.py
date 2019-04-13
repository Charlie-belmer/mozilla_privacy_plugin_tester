"""
Test plugins and determine which, if any, URL's are used to syphon data
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, TimeoutException

from zapv2 import ZAPv2

import urllib.request
import imghdr
import shutil
import os
import re
import time

from db import get_plugins_to_test, store_test_results

target = 'http://127.0.0.1'
api_key = os.getenv("API_KEY", "58b3r23uoggmchnsu2jg7mfcdl")
localProxy = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}

zap = ZAPv2(proxies=localProxy, apikey=api_key)
core = zap.core

proxyString = "localhost:8080"

desired_capability = webdriver.DesiredCapabilities.FIREFOX
desired_capability['proxy'] = {
    "proxyType": "manual",
    "httpProxy": proxyString,
    "ftpProxy": proxyString,
    "sslProxy": proxyString
}
binary = "/usr/bin/firefox"
test_site_list = [
    {"url": "https://www.wikipedia.org", "exclude_patterns": [".*\.wikipedia\.org"]},
    {"url": "https://duckduckgo.com", "exclude_patterns": [".*\.duckduckgo\.com", "https://duckduckgo.com"]},
    {"exclude_patterns": [".*\.firefox\.com", ".*\.mozilla\.com", ".*\.mozilla\.net", ".*\.mozilla\.org", "*safebrowsing\.googleapis\.com"]}
]

def download_plugin(name, url, icon_url):
    """Download plugin xpi and icon files"""

    # clean up characters in name
    name = name.replace(" ", "_")
    for c in "/;:,@":
        name = name.replace(c, "")
    filename = "addons/" + name + ".xpi"
    try:
        urllib.request.urlretrieve(url, filename)
        temp_file, headers = urllib.request.urlretrieve(icon_url)
        icon_name = "addons/" + name + "_icon." + imghdr.what(temp_file)
        shutil.copyfile(temp_file, icon_name)
        os.remove(temp_file)
    except urllib.error.HTTPError:
        print("Error retrieving plugin. You may need to update crawl data")
        return None
    return {"icon_file": icon_name, "xpi_file": filename}

def test_plugin_requests(extension_path):
    """Load a clean browser with the extension, and visit some pages through the proxy"""
    driver = webdriver.Firefox(firefox_binary=binary, executable_path='./geckodriver', capabilities=desired_capability)
    try:
        ext_id = driver.install_addon(extension_path, temporary=True)
        # Plugin may load "welcome" page, which we don't want to include here.
        time.sleep(5) # Give page time to load
        if len(driver.window_handles) > 1:
            for handle in driver.window_handles[1:]:
                driver.switch_to_window(handle)
                driver.close()
        driver.switch_to_window(driver.window_handles[0])
        # Now that we have closed any possible welcome pages, start tracking new URL's
        core.new_session(name="plugin_test", overwrite=True)

        for test in test_site_list:
            if "url" in test.keys():
                driver.get(test["url"])
    except WebDriverException as e:
        print("Error installing plugin: ")
        print(e)
        driver.quit()
        return None
    except TimeoutException as e:
        print("Test timeout. Pausing execution for 5 minutes")
        print(e)
        time.sleep(300)
    driver.quit()
    return core.sites

def exclude_whitelist_results(visited_sites):
    """Removes any whitelisted sites from the visited list"""
    remove_list = []
    for test in test_site_list:
        for exclude_pattern in test["exclude_patterns"]:
            for site in visited_sites:
                if re.search(exclude_pattern, site) is not None:
                    remove_list.append(site)
    for site in remove_list:
        visited_sites.remove(site)
    return visited_sites

def get_messages(scoped_sites):
    """get message traffic from sites in scope"""
    findings = {}
    for site in scoped_sites:
        messages = core.messages(site)
        findings[site] = []
        if messages == 'internal_error':
            # If the proxy doesn't handle the output without crashing (wierd issue with Norton CDN, need zaproxy fix)
            # This only happens in zaproxy daemon mode
            findings[site].append({"header": "Internal proxy error. Check manually", "body": "Internal proxy error. Check manually"})
            continue
        for message in messages:
            findings[site].append({"header": message["requestHeader"], "body": bytes(str(message["requestBody"]), 'UTF8')})
    return findings

def test_plugin(plugin_name, xpi_url, icon_url, plugin_id):
    """Main test function - runs end to end test and stores results"""
    files = download_plugin(plugin_name, xpi_url, icon_url)
    if files is None:
        return
    extension_path = os.path.dirname(os.path.realpath(__file__)) + "/" + files["xpi_file"]
    visited_sites = test_plugin_requests(extension_path)
    if visited_sites is None:
        return
    visited_sites = exclude_whitelist_results(visited_sites)
    findings = get_messages(visited_sites)
    store_test_results(plugin_id, files["icon_file"], findings)
