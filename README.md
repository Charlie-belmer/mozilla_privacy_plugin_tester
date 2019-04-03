# extension_privacy_tester

scrape and test all firefox plugins for privacy concerns by seeing what data is collected and sent. 

This project automates the process of finding plugins (currently with more than 1000 installs), installing each plugin within a fresh Firefox browser, and then monitoring traffic via the ZAP proxy as the browser navigates to a few pages. It then saves the data that was transmitted by the plugin for review.

## Getting the project setup

This project requires python3 with pipenv. Once python is installed in your system, you can install the environment by running:
```
pipenv install
```
from the project root.

The project also depends on a postgres install. Configure a new user and run the db_setup.sql script to create the necessary tables. Once created, set your environment variables for the following:
```bash
export DB_USER=<username>
export DB_PASS=<password>
export DB_PORT=<postgres_port (defaults to 5432 if unset)>
export DB_HOST=<db_host (defaults to localhost if unset)>
export DB_NAME=<db_name (defaults to 'plugins' if unset)>
```

There should be a recent firefox binary for selenium in the repository, but if you get any firefox errors, you may have to find and update to the latest driver file
```
https://github.com/mozilla/geckodriver
```

install ZAP. If you are running a snap supported linux version
```bash
sudo snap install zaproxy --classic
```
Otherwise refer to the homepage for installation instructions.

## Running the project locally

Running the crawler. This will create a json file with information about all plugins with more than 1000 users.

```bash
cd crawler
pipenv run scrapy crawl privacy_monitor -o plugins.json
```

Start ZAP in headless mode

```
zaproxy -daemon -host 0.0.0.0 -port 8080
```

Run the ingestor and then the tester:
```bash
pipenv run main.py -i
pipenv run main.py -t
```
## Future potential enhancements
 * Integrate crawl funcionality into main
 * Increase test coverage - searches, additional sites
 * Add testing when plugin is "clicked" if possible

## considerations when querying data
Message bodys are stored as byte arrays, since some data POSTed by plugins may include null bytes, which are not supported in Postgres TEXT types. To query that table
and view as text, use the following query:

```sql
select encode(body, 'escape') as body from test_messages
```