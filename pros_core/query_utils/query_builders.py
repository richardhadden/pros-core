import neomodel
from pros_core.models import AbstractNode
from pros_core.setup_app import ModelManager

EXCLUDE_FROM_PROPERTY_UNPACKING = {"last_dependent_change"}


def build_unpack_properties_string(model: AbstractNode):
    return ", ".join(
        f".{property}"
        for property in ModelManager(model).properties
        if property not in EXCLUDE_FROM_PROPERTY_UNPACKING
    )


def build_outward_relation_calls_and_unpacking(
    model: AbstractNode, cypher_node_variable: str
) -> tuple[str, str]:
    """Builds a sub-query call and unpacking string for outward relation from a node.

    Args:
    - model: the model of the node requested;
    - cypher_node_variable: the name of the node in the enclosing cypher query to use as a starting point

    Returns:
    - calls string: the Call subquery
    - unpacking string: string to unpack the results of subquery into the parent node"""

    outward_relations = ModelManager(model).relationships

    calls_string = ""
    for _, relationship in outward_relations.items():
        properties_unpacking = build_unpack_properties_string(relationship.target_model)

        relationship_data_unpacking = ""
        if relationship.has_relation_data:
            relation_property_unpacking = ", ".join(
                f".{prop}" for prop in relationship.relation_properties
            )
            relationship_data_unpacking = f", _relationship_data:{relationship.relation_label}_relation{{{relation_property_unpacking}}}"

        calls_string += f"""
        CALL {{
            WITH {cypher_node_variable}
            MATCH ({cypher_node_variable})-[{relationship.relation_label}_relation:{relationship.relation_label}]->({relationship.relation_label.lower()}_internal)
            RETURN 
                COLLECT({relationship.relation_label.lower()}_internal{{.uid, {properties_unpacking} {relationship_data_unpacking} }}) AS {relationship.relation_label.lower()}
                        
        }}
        """
    unpacking_string = ", ".join(
        f"{relationship.relation_label.lower()}:{relationship.relation_label.lower()}"
        for _, relationship in outward_relations.items()
    )
    if unpacking_string:
        unpacking_string = ", " + unpacking_string

    return calls_string, unpacking_string


def build_child_node_calls_and_unpacking(model: AbstractNode) -> tuple[str, str]:
    child_nodes = ModelManager(model).child_nodes

    calls_string = ""
    for child_node_name, child_node in child_nodes.items():
        # NOW get OUTWARD rels from child_node.child_model! n.b. nothing can point inwards to child nodes!
        (
            outward_relation_calls_string,
            outward_relation_unpacking_string,
        ) = build_outward_relation_calls_and_unpacking(
            child_node.child_model, f"{child_node_name}_internal"
        )

        properties_unpacking = build_unpack_properties_string(child_node.child_model)

        calls_string += f"""
        CALL {{
            WITH matched_node
            MATCH (matched_node)-[:{child_node.relation_label}]->({child_node_name}_internal)
            {outward_relation_calls_string}
            RETURN COLLECT({child_node_name}_internal{{.uid, {properties_unpacking}{outward_relation_unpacking_string}}}) as {child_node_name}
        }}
        """
    unpacking_string = ", ".join(
        f"{child_node_name}:{child_node_name}" for child_node_name in child_nodes
    )
    if unpacking_string:
        unpacking_string = ", " + unpacking_string

    return calls_string, unpacking_string


def build_reverse_relation_calls_and_unpacking(
    model: AbstractNode, cypher_node_variable="matched_node"
) -> str:
    reverse_relations = ModelManager(model).reverse_relationships

    calls_string = ""
    for reverse_relation_name, reverse_relation in reverse_relations.items():
        forward_name = reverse_relation["relationship_forward_name"]

        properties_unpacking = build_unpack_properties_string(
            ModelManager(reverse_relation["relation_to"]).model_class
        )
        # TODO: Rewrite reversion_relations not as dict; also need to have the model fields on them too
        calls_string += f"""
        CALL {{
            WITH {cypher_node_variable}
            MATCH ({cypher_node_variable})<-[:{forward_name}]-({reverse_relation_name}_internal)
            RETURN COLLECT({reverse_relation_name}_internal{{.uid, {properties_unpacking}}}) AS {reverse_relation_name}
        }}
        """
    unpacking_string = ", ".join(
        f"{reverse_relation_name}:{reverse_relation_name}"
        for reverse_relation_name in reverse_relations
    )
    if unpacking_string:
        unpacking_string = ", " + unpacking_string

    return calls_string, unpacking_string


def build_abstract_reification_calls_and_unpacking(
    model: AbstractNode, cypher_node_variable="matched_node"
):
    related_reifications = ModelManager(model).related_reifications

    calls_string = ""
    for related_reification_name, related_reification in related_reifications.items():
        pass

        calls_string += f"""
            CALL {{
                WITH {cypher_node_variable}
                MATCH ({cypher_node_variable})-[:{related_reification.relation_label}]->({related_reification_name}_internal)
                
            }}
        
        
        """


def build_read_query_cypher(model: AbstractNode) -> str:
    (
        child_node_calls_string,
        child_node_unpacking,
    ) = build_child_node_calls_and_unpacking(model)
    (
        outward_related_node_calls_string,
        outward_related_node_unpacking,
    ) = build_outward_relation_calls_and_unpacking(model, "matched_node")
    (
        reverse_relations_calls_string,
        reverse_relations_unpacking,
    ) = build_reverse_relation_calls_and_unpacking(model)

    properties_unpacking = build_unpack_properties_string(model)

    query = f"""
    MATCH (matched_node:{model.__name__} {{uid: $uid}})
    {outward_related_node_calls_string}
    {child_node_calls_string}
    {reverse_relations_calls_string}
    RETURN matched_node{{.uid, {properties_unpacking}{child_node_unpacking}{outward_related_node_unpacking}{reverse_relations_unpacking}}}
    """
    return query


def build_read_query(model):
    def read_query(cls, uid):
        query = build_read_query_cypher(model)
        # print("Q", query)
        result, meta = neomodel.db.cypher_query(query, {"uid": uid})
        # print(meta)
        return result[0][0]

    return read_query
