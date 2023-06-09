import docker
import neomodel
import pytest

client = docker.from_env()

from neomodel import config

config.DATABASE_URL = "bolt://neo4j:test@localhost:7688"


@pytest.fixture(scope="session", autouse=True)
def db():
    import os
    import subprocess
    import time

    already_running = False
    try:
        container = client.containers.get("pros_test_neo4j")
        if container.status != "running":
            raise Exception()
        else:
            already_running = True
    except:
        try:
            client.containers.get("pros_test_neo4j")
            subprocess.run(["docker", "start", "pros_test_neo4j"])
        except:
            p = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(["sh", f"{p}/start_neo4j.sh"])
        container = client.containers.get("pros_test_neo4j")
        while container.status != "running":
            time.sleep(1)
        while True:
            try:
                neomodel.install_all_labels()
                break
            except:
                time.sleep(1)
    yield
    if not already_running:
        subprocess.run(["docker", "stop", "pros_test_neo4j"])


@pytest.fixture()
def clear_db():
    from neomodel import db

    neomodel.clear_neo4j_database(db, clear_constraints=True, clear_indexes=True)
    neomodel.install_all_labels()
    yield
    # neomodel.clear_neo4j_database(db, clear_constraints=True, clear_indexes=True)
