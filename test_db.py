# test_db.py
from database import engine
from sqlalchemy import text

print("Pinging MariaDB socket interface via SQLAlchemy engine...")
try:
    with engine.connect() as connection:
        # Query database description parameters for active structural validation
        result = connection.execute(text("DESCRIBE Service_Reports_Signatures;"))
        print("\n🎉 Connection Successful! Core Table Layout Discovered:")
        for column in result:
            print(f" Column Field Name: {column[0]} | Data Type Spec: {column[1]}")
except Exception as e:
    print(f"\n❌ Pipeline Connection Failure: {e}")
