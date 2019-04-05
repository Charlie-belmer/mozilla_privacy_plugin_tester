import psycopg2
from psycopg2.pool import ThreadedConnectionPool
import os
import time

db_user = os.getenv("DB_USER", '')
db_pass = os.getenv("DB_PASS", '')
db_port = os.getenv("DB_PORT", "5432")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "plugins")

min_connections = 1
max_connections = 10

kwargs = {
    "host": db_host,
    "user": db_user,
    "password": db_pass,
    "dbname": db_name,
    "port": db_port
}
pool = ThreadedConnectionPool(min_connections, max_connections, **kwargs)

def get_plugins_to_test():
    """
    Gets the next plugin that needs testing. We know a plugin needs testing if:
        * there is no test record in the DB for a given plugin in the plugin_repository table OR
        * the test result timestamp is older than the 
    """
    query = """
        SELECT name, repo.id, xpi_url, icon_url
        FROM 
            plugin_repository repo LEFT OUTER JOIN
            test_results tests ON tests.plugin = repo.id
        WHERE
            tests.last_test_date < repo.last_plugin_update OR
            tests.last_test_date IS NULL
        ORDER BY
            repo.users DESC
    """
    conn = pool.getconn()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    pool.putconn(conn)
    rows = [{"name": a,
             "id": b,
             "url": c,
             "icon_url": d} for (a, b, c, d) in rows]
    return rows

def get_test_result_id(plugin_id):
    query = """
        SELECT id
        FROM test_results
        WHERE plugin = %(plugin_id)s
        """
    conn = pool.getconn()
    cur = conn.cursor()
    data = {
        "plugin_id": plugin_id
    }
    cur.execute(query, data)
    rows = cur.fetchall()
    cur.close()
    pool.putconn(conn)
    if len(rows) == 0:
        return None
    else:
        return rows[0][0]

def search_plugin_id(name, author):
    select = """
        SELECT id
        FROM plugin_repository
        WHERE name = %s AND author = %s
        """
    conn = pool.getconn()
    cur = conn.cursor()
    cur.execute(select, (name, author))
    rows = cur.fetchall()
    cur.close()
    pool.putconn(conn)
    if len(rows) > 0:
        return rows[0][0]
    else:
        return None

def update_test_result(test_id, plugin_id, findings, icon_path):
    """Update - just delete old records and re-insert new. Not keeping any old records"""
    query = """
        DELETE FROM test_results WHERE plugin = %s
        """
    conn = pool.getconn()
    cur = conn.cursor()
    cur.execute(query, (plugin_id, ))
    conn.commit()
    cur.close()
    pool.putconn(conn)
    insert_test_results(plugin_id, icon_path, findings)

def update_plugin(plugin):
    update = """
        UPDATE plugin_repository
        SET
            icon_url = %(icon_url)s,
            xpi_url = %(xpi_url)s,
            users = %(users)s,
            version = %(version)s,
            last_plugin_update = %(last_updated)s
        WHERE
            id = %(id)s
        """
    conn = pool.getconn()
    cur = conn.cursor()
    cur.execute(update, plugin)
    conn.commit()
    cur.close()
    pool.putconn(conn)

def insert_test_results(plugin_id, icon_path, findings):
    conn = pool.getconn()
    cur = conn.cursor()
    test_query = """
        INSERT INTO test_results 
            (
                icon_path,
                plugin,
                last_test_date
            )
        VALUES
            (
                %(icon_path)s,
                %(plugin_id)s,
                %(last_test_date)s
            )
        RETURNING id
        """
    date = time.strftime("%m/%d/%Y")
    data = {
        "plugin_id": plugin_id,
        "icon_path": icon_path,
        "last_test_date": date
    }
    cur.execute(test_query, data)
    test_id = cur.fetchone()[0]

    url_query = """
        INSERT INTO test_results_urls
            (
                url,
                test_id
            )
        VALUES
            (
                %(url)s,
                %(test_id)s
            )
        RETURNING id
        """

    message_query = """
        INSERT INTO test_messages
            (
                header,
                body,
                url_id
            )
        VALUES
            (
                %(header)s,
                %(body)s,
                %(url_id)s
            )
        """
    for url, messages in findings.items():
        url_data = {
            "url": url,
            "test_id": test_id
        }
        cur.execute(url_query, url_data)
        url_id = cur.fetchone()[0]
        for message in messages:
            message_data = {
                "header": message["header"],
                "body": message["body"],
                "url_id": url_id
            }
            print("inserting URL " + url)
            print("header: " + message["header"])
            #import pdb;pdb.set_trace()
            cur.execute(message_query, message_data)
    conn.commit()
    cur.close()
    pool.putconn(conn)

def insert_plugin(plugin):
    insert = """
        INSERT INTO plugin_repository (
                        name,
                        url,
                        icon_url,
                        xpi_url,
                        users,
                        author,
                        version,
                        last_plugin_update
                    )
        VALUES (
                %(name)s,
                %(url)s,
                %(icon_url)s,
                %(xpi_url)s,
                %(users)s,
                %(author)s,
                %(version)s,
                %(last_updated)s
            )
        """
    conn = pool.getconn()
    cur = conn.cursor()
    cur.execute(insert, plugin)
    conn.commit()
    cur.close()
    pool.putconn(conn)

def pull_report():
    query = """
SELECT 
    repo.name, 
    repo.author, 
    repo.version, 
    repo.users, 
    tests.icon_path, 
    count(findings.test_id) as total_requests,
    '<table>' || string_agg(findings.d, '') || '</table>' as urls, 
    repo.last_plugin_update, 
    tests.last_test_date
FROM 
    plugin_repository repo,
    test_results tests LEFT OUTER JOIN
    (SELECT 
        url_findings.test_id as test_id,
        '<tr><td>' || url_findings.url || '</td></tr><tr><td>' || messages.header || '</td></tr><tr><td>' || messages.body || '</td></tr>' as d
     FROM 
        test_results_urls url_findings,
        test_messages messages
     WHERE
        messages.url_id = url_findings.id
    ) findings ON findings.test_id = tests.id
    
WHERE
    tests.plugin = repo.id AND
    tests.last_test_date IS NOT NULL
GROUP BY
    repo.name, 
    repo.author, 
    repo.version, 
    repo.users, 
    tests.icon_path, 
    repo.last_plugin_update, 
    tests.last_test_date
ORDER BY
    repo.users DESC
    """
    conn = pool.getconn()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    pool.putconn(conn)
    rows = [{
                 "name": a,
                 "author": b,
                 "version": c,
                 "users": d,
                 "icon": e,
                 "request_count": f,
                 "requests": g,
                 "last_plugin_update": h.strftime("%m/%d/%Y"),
                 "last_test_date": i.strftime("%m/%d/%Y")
             } for (a, b, c, d, e, f, g, h, i) in rows]
    return rows

def store_test_results(plugin_id, icon_path, findings):
    test_id = get_test_result_id(plugin_id)
    if test_id is None:
        insert_test_results(plugin_id, icon_path, findings)
    else:
        update_test_result(test_id, plugin_id, findings, icon_path)

def store_plugin(plugin):
    plugin_id = search_plugin_id(plugin['name'], plugin['author'])
    if plugin_id is None:
        insert_plugin(plugin)
    else:
        plugin["id"] = plugin_id
        update_plugin(plugin)