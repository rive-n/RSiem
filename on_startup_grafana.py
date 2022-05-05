from grafana_client import GrafanaApi
from grafana_client.client import GrafanaClientError
from os import environ, path
from functools import lru_cache
from ujson import load

if environ.get('DEBUG') == 'true':
    creds = ("Riven", "Riven")
    host = "localhost:3000"
else:
    creds = environ.get("GF_USERNAME"), environ.get("GF_PASSWORD")
    if not creds:
        raise KeyError("Check environ variables")
    host = "grafana:3000"

client = GrafanaApi(
    auth=creds,
    host=host
)


def create_datasource_request():
    # env:
    # - PSQL_USERNAME
    # - PSQL_PASSWORD
    # - DEBUG

    if environ.get("DEBUG") == "true":
        psql_host, psql_username, psql_password = "localhost:5432", "grafana", "grafana"
    else:
        psql_host, psql_username, psql_password = "postgres:5432", environ.get('PSQL_USERNAME'), \
                                                  environ.get('PSQL_PASSWORD')
    try:
        source = client.datasource.create_datasource({"name": "PostgreSQL", "type": "postgres",
                                                      "access": "proxy", "isDefault": True})['datasource']
    except GrafanaClientError as e:
        print("Error: ", e)
        print("Seems like datasource already exists, trying to hook it.")
        source = client.datasource.get_datasource_by_name("PostgreSQL")
    source_uid, source_id, source_version = source['uid'], source['id'], source['version'] + 1
    client.datasource.update_datasource(source_id,
                                        {"id": source_id, "uid": source_uid, "orgId": 1, "name": "PostgreSQL",
                                         "type": "postgres",
                                         "typeLogoUrl": "", "access": "proxy", "url": psql_host,
                                         "password": psql_password,
                                         "user": psql_username, "database": "grafana", "basicAuth": False,
                                         "basicAuthUser": "",
                                         "basicAuthPassword": "", "withCredentials": False, "isDefault": True,
                                         "jsonData": {"postgresVersion": 903, "sslmode": "disable", "tlsAuth": False,
                                                      "tlsAuthWithCACert": False, "tlsConfigurationMethod": "file-path",
                                                      "tlsSkipVerify": True}, "secureJsonFields": {},
                                         "version": source_version,
                                         "readOnly": True,
                                         "secureJsonData": {"password": "grafana"}})


@lru_cache()
def create_and_configure_dashboard(dash_name: bool = None):
    if environ.get('DEBUG'):
        abs_path = path.abspath("deploy/grafana/dashboard.json")
    else:
        abs_path = path.join(environ.get('ROOT_PATH'), "deploy/grafana/dashboard.json")
    if not path.isfile(abs_path):
        print("File does not exist")
        exit(-1)

    with open(abs_path, "r") as stream:
        dashboard_config = load(stream)

    if dash_name:
        dashboard_config['dashboard']['title'] += 'CP'
    try:
        client.client.POST('/dashboards/db/', dashboard_config)
    except GrafanaClientError as e:
        print("Seems like this dashboard already exists, creating copy with CP on end")
        create_and_configure_dashboard(True)


if __name__ == '__main__':
    create_datasource_request()
    create_and_configure_dashboard()
