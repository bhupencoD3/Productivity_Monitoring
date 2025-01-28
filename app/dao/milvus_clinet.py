from pymilvus import (
    Collection,
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)


class MilvusClient:
    def __init__(self, collection_name):
        # Connect to Milvus
        connections.connect(
            "default", host="localhost", port="19530"
        )  # Adjust host and port as needed
        self.collection_name = collection_name
        self.collection = self._create_collection()

    def _create_collection(self):
        # Check if the collection already exists
        if utility.has_collection(self.collection_name):
            print(f"Collection '{self.collection_name}' already exists.")
            return Collection(self.collection_name)

        # Define the schema for the collection
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(
                name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512
            ),  # Adjust dim based on your model
        ]
        schema = CollectionSchema(fields, description="Face embeddings collection")
        collection = Collection(name=self.collection_name, schema=schema)
        print(f"Collection '{self.collection_name}' created.")
        return collection

    def insert_embeddings(self, embeddings):
        # Insert embeddings into the collection
        if not isinstance(embeddings, list):
            raise ValueError("Embeddings should be a list of vectors.")

        ids = self.collection.insert([embeddings])
        print(f"Inserted {len(ids)} embeddings into '{self.collection_name}'.")
        return ids

    def search_embedding(self, embedding, limit=5):
        # Search for the closest embeddings
        if not isinstance(embedding, list):
            raise ValueError("Embedding should be a list vector.")

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            [embedding], "embedding", search_params, limit=limit
        )
        return results

    def drop_collection(self):
        # Drop the collection
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' dropped.")
        else:
            print(f"Collection '{self.collection_name}' does not exist.")

    def __del__(self):
        # Disconnect from Milvus when the object is deleted
        connections.disconnect("default")
        print("Disconnected from Milvus.")
