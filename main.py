from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from zapv2 import ZAPv2
target = 'http://127.0.0.1'
api_key = "58b3r23uoggmchnsu2jg7mfcdl"
localProxy = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
zap = ZAPv2(proxies=localProxy, apikey=api_key)
core = zap.core
core.new_session(name="nice_test", overwrite=True)

proxyString = "localhost:8080"

desired_capability = webdriver.DesiredCapabilities.FIREFOX
desired_capability['proxy'] = {
    "proxyType": "manual",
    "httpProxy": proxyString,
    "ftpProxy": proxyString,
    "sslProxy": proxyString
}
binary = "/usr/bin/firefox"
driver = webdriver.Firefox(firefox_binary=binary, executable_path='./geckodriver', capabilities=desired_capability)
extension_path = "/home/shade/projects/extension-test/addons/ublock_origin-1.18.0-an+fx.xpi"
ext_id = driver.install_addon(extension_path, temporary=True)
driver.get("http://www.python.org")
assert "Python" in driver.title
elem = driver.find_element_by_name("q")
elem.clear()
elem.send_keys("pycon")
elem.send_keys(Keys.RETURN)
assert "No results found." not in driver.page_source
driver.close()
import pdb;pdb.set_trace()
print(core.sites) # list of all sites visited!