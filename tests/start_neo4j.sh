#docker run --name testneo4j  -p7474:7474 -p7687:7687 \
#-d \
#-v $HOME/neo4j/data:/data \
#-v $HOME/neo4j/logs:/logs \
#-v $HOME/neo4j/import:/var/lib/neo4j/import \
#-v $HOME/neo4j/plugins:/plugins \
#--env NEO4J_AUTH=neo4j/test \
#neo4j:latest


docker run --name pros_test_neo4j \
    --user="$(id -u)":"$(id -g)" \
    --env 'NEO4J_PLUGINS=["apoc"]' \
    -p 7474:7474 -p 7688:7687 \
    -v $PWD/neo4j/data:/data \
    -v $PWD/neo4j/logs:/logs \
    -v $PWD/neo4j/import:/var/lib/neo4j/import \
    -v NEO4J_apoc_ttl_enabled=false \
    -e NEO4J_server_config_strict__validation_enabled=false \
    -e  NEO4J_dbms_databases_seed__from__uri__providers=false \
    --env NEO4J_AUTH=neo4j/test \
    neo4j:latest

  #-e NEO4J_apoc_export_file_enabled=true \
    #-e NEO4J_apoc_import_file_enabled=true \