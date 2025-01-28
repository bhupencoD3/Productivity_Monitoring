from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType

MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "employee_faces"


class UserClient:
    def __init__(self):
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """
        Get or create the Milvus collection for storing employee embeddings.
        """
        if COLLECTION_NAME not in [col.name for col in Collection.list()]:
            fields = [
                FieldSchema(
                    name="name", dtype=DataType.VARCHAR, max_length=100, is_primary=True
                ),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512),
            ]
            schema = CollectionSchema(fields, description="Employee face embeddings")
            return Collection(name=COLLECTION_NAME, schema=schema)
        return Collection(COLLECTION_NAME)

    def insert_employee(self, name: str, embedding: list):
        """
        Insert an employee's embedding into Milvus.
        """
        self.collection.insert([[name], [embedding]])

    def list_employees(self):
        """
        List all employees stored in Milvus.
        """
        result = self.collection.query(expr=None, output_fields=["name"])
        return [record["name"] for record in result]

    def delete_employee(self, name: str):
        """
        Delete an employee from Milvus by name.
        """
        self.collection.delete(expr=f"name == '{name}'")

    def search_employee(self, embedding: list, limit=1):
        """
        Search for an employee by embedding in the database.
        """
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=limit,
        )
        if results and results[0]:
            closest_match = results[0][0]
            return {
                "name": closest_match.entity.get("name", "Unknown"),
                "distance": closest_match.distance,
            }
        return {"name": "Unknown", "distance": None}
