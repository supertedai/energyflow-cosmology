import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')))

with driver.session() as session:
    print('🔍 Familie/barnenoder:')
    result = session.run("""
        MATCH (p:Person)-[r:FAMILY|PARENT_OF|CHILD_OF|SPOUSE_OF]->(c)
        RETURN p.name, type(r), c.name LIMIT 30
    """)
    for row in result:
        print(row)
driver.close()
