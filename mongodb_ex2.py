# import relevant modules
import re
from pathlib import Path
from pymongo import MongoClient
from datetime import datetime



# add the main function to call the debug_test_attempt function
if __name__ == '__main__':
    # Create a connection to the MongoDB server
    client = MongoClient('mongodb://localhost:27017/')

    # Get a reference to your database
    db = client.test_harmony_database

    # Get a reference to your collection
    collection_name = "tdy"

    collection = db[collection_name]

    # Find all unique test_names
    test_names = collection.distinct("test_name")

    # Initialize an empty list to store the results
    results = []

    # Loop over all unique test_names to calculate the PASS and FAIL count
    for test_name in test_names:
        # Count documents with the specified test_name and a final_verdict with the string value PASS
        pass_count = collection.count_documents({"test_name": test_name, "final_verdict": "PASS"})
        
        # pass_count = collection.count_documents({"test_name": test_name, "PASS": {"$gt": 0}})
        
        # Count documents with the specified test_name and a final_verdict with the string value FAIL
        fail_count = collection.count_documents({"test_name": test_name, "final_verdict": "FAIL"})
        #fail_count = collection.count_documents({"test_name": test_name, "FAIL": {"$gt": 0}})
        
        # Create a dictionary with the test_name and its PASS and FAIL count
        result = {
            "test_name": test_name,
            "pass_count": pass_count,
            "fail_count": fail_count
        }
        
        # Append the dictionary to the results list
        results.append(result)

    # Print the results
    for res in results:
        print(f"Test Name: '{res['test_name']}' | PASS Count: {res['pass_count']} | FAIL Count: {res['fail_count']}")
        
    # # Define the aggregation pipeline
    # pipeline = [
    #     {
    #         "$group": {
    #             "_id": "$test_name",
    #             "total_passes": {"$sum": "$PASS"},
    #             "total_fails": {"$sum": "$FAIL"}
    #         }
    #     },
    #     {
    #         "$project": {
    #             "test_name": "$_id",
    #             "fail_to_pass_ratio": {
    #                 "$cond": [
    #                     {"$eq": ["$total_passes", 0]},
    #                     "Infinity",
    #                     {"$divide": ["$total_fails", "$total_passes"]}
    #                 ]
    #             }
    #         }
    #     },
    #     {
    #         "$sort": {"fail_to_pass_ratio": -1}
    #     },
    #     {
    #         "$limit": 5
    #     }
    # ]

    # # Execute the aggregation pipeline
    # result = collection.aggregate(pipeline)

    # # Print the result
    # for doc in result:
    #     print(doc)

    test_name_to_find = "HCI_CIN_BV_11"

    # Query to find all documents with the specified test_name
    query = {"test_name": test_name_to_find}

    # Find all the documents matching the query
    results = collection.find(query)

    # Print out all the attempts for the specified test_name
    for result in results:
        print(result)

    