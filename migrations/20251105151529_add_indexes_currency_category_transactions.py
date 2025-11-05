"""
Migration: add_indexes_currency_category_transactions
Created: 2025-11-05 15:15:29

Adds indexes to the 'transactions' collection:
- Index on 'currency' field (standard B-tree index) - for required enum field with limited values
- Index on 'category' field (sparse index) - for optional field that may be absent in some documents
"""

from nauta_migrations.migrate import BaseMigration


class Migration(BaseMigration):
    """Add indexes to currency and category fields in transactions collection"""
    
    def upgrade(self):
        """
        Create indexes on currency and category fields in the transactions collection.
        """
        collection_name = "transactions"
        
        try:
            # Verify collection exists
            if collection_name not in self.db.list_collection_names():
                print(f"Collection '{collection_name}' does not exist. Cannot create indexes.")
                return
            
            collection = self.db[collection_name]
            
            # Get existing indexes to avoid duplicates
            existing_indexes = [idx["name"] for idx in collection.list_indexes()]
            
            # Create index on currency field (standard B-tree index)
            # Appropriate for required enum fields with limited values
            if "currency_1" not in existing_indexes:
                collection.create_index("currency")
                print(f"Index created on 'currency' field in '{collection_name}' collection")
            else:
                print(f"Index on 'currency' field already exists. Skipping.")
            
            # Create sparse index on category field
            # Efficient for optional fields that may be absent in some documents
            if "category_1" not in existing_indexes:
                collection.create_index("category", sparse=True)
                print(f"Sparse index created on 'category' field in '{collection_name}' collection")
            else:
                print(f"Index on 'category' field already exists. Skipping.")
            
        except Exception as e:
            print(f"Error creating indexes in '{collection_name}' collection: {e}")
            raise
    
    def downgrade(self):
        """
        Remove indexes from currency and category fields in the transactions collection.
        """
        collection_name = "transactions"
        
        try:
            # Verify collection exists
            if collection_name not in self.db.list_collection_names():
                print(f"Collection '{collection_name}' does not exist. Nothing to do.")
                return
            
            collection = self.db[collection_name]
            
            # Get existing indexes
            existing_indexes = {idx["name"]: idx for idx in collection.list_indexes()}
            
            # Drop index on currency field
            if "currency_1" in existing_indexes:
                collection.drop_index("currency_1")
                print(f"Index dropped on 'currency' field in '{collection_name}' collection")
            else:
                print(f"Index on 'currency' field does not exist. Nothing to drop.")
            
            # Drop sparse index on category field
            if "category_1" in existing_indexes:
                collection.drop_index("category_1")
                print(f"Sparse index dropped on 'category' field in '{collection_name}' collection")
            else:
                print(f"Index on 'category' field does not exist. Nothing to drop.")
            
        except Exception as e:
            print(f"Error dropping indexes in '{collection_name}' collection: {e}")
            raise

