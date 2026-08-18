import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
AUTH = (GRAFANA_USER, GRAFANA_PASSWORD)

# Direct local network references inside Docker space or standard ports
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "repomind-postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "repomind")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")


def create_datasource() -> str:
    """Create or update the PostgreSQL datasource in Grafana."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "name": "repomind-postgres",
        "type": "postgres",
        "url": f"{POSTGRES_HOST}:{POSTGRES_PORT}",
        "access": "proxy",
        "user": POSTGRES_USER,
        "database": POSTGRES_DB,
        "secureJsonData": {"password": POSTGRES_PASSWORD},
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 1700,
            "timescaledb": False,
        },
        "isDefault": True,
        "editable": True,
    }

    # Check if datasource already exists
    check_response = requests.get(
        f"{GRAFANA_URL}/api/datasources/name/repomind-postgres", auth=AUTH
    )
    if check_response.status_code == 200:
        print("Datasource already exists, updating...")
        ds_id = check_response.json()["id"]
        response = requests.put(
            f"{GRAFANA_URL}/api/datasources/{ds_id}",
            json=payload,
            headers=headers,
            auth=AUTH,
        )
        print(f"Datasource update status: {response.status_code}")
        return response.json().get("datasource", {}).get("uid", "")
    else:
        print("Creating new PostgreSQL datasource...")
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            json=payload,
            headers=headers,
            auth=AUTH,
        )
        print(f"Datasource creation status: {response.status_code}")
        return response.json().get("datasource", {}).get("uid", "")


def import_dashboard(datasource_uid: str) -> None:
    """Read the local dashboard definition and register it dynamically with the datasource."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.json")
    with open(dashboard_path, encoding="utf-8") as f:
        dashboard = json.load(f)

    # Walk panels and update datasource fields
    def update_datasource(obj):
        if isinstance(obj, dict):
            if "datasource" in obj and isinstance(obj["datasource"], dict):
                if obj["datasource"].get("type") == "postgres":
                    obj["datasource"]["uid"] = datasource_uid
            for val in obj.values():
                update_datasource(val)
        elif isinstance(obj, list):
            for item in obj:
                update_datasource(item)

    update_datasource(dashboard)

    headers = {"Content-Type": "application/json"}
    payload = {
        "dashboard": dashboard,
        "overwrite": True,
    }

    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        json=payload,
        headers=headers,
        auth=AUTH,
    )
    print(f"Dashboard import status: {response.status_code}, {response.text}")


if __name__ == "__main__":
    print("Starting Grafana dynamic provisioning...")
    try:
        ds_uid = create_datasource()
        if ds_uid:
            import_dashboard(ds_uid)
            print("Successfully provisioned PostgreSQL datasource and dashboard.")
            print(f"Verify dashboards locally at: {GRAFANA_URL}")
        else:
            print("Failed to retrieve datasource UID.")
    except Exception as exc:
        print(f"Provisioning failed: {exc}")
