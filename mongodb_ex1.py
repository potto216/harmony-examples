# import relevant modules
import re
from pathlib import Path
from pymongo import MongoClient
from datetime import datetime

# a pymongo program that creates a  way to track the passes and fails and reasons for the fail for a collection of tests. Each test will have a 
# unique test name. A test can be run multiple times. Each run may consist of one or more attempts. Each attempt will result in a pass or fail.
# We would like to look at statistics such as the number of pass and fails of a test and compare those to other tests. Also for each attempt the
# relative directory path should be stored so the data files for that attempt can be referenced later.


# This function creates a list of test collection runs. The function has a parameter that is an absolute root path which is a path object. The function 
# looks to see if this path contains a directory called 'Results'. 
# If so it creates a list of all subdirectories of 'Results' that are in the regular expression format `Run_\d{8}_\d{9}` and returns the list of names. 
# These names are the names of the test collection runs.
# An example would be `Run_20230303_084230899` . If there are none it returns an empty list.
def get_test_collection_runs(root_path):
    """Get a list of test collection runs."""
    test_collection_runs = []
    results_folder_name = Path('Results')
    results_path = root_path / results_folder_name
    if results_path.exists():
        for path in results_path.iterdir():
            if path.is_dir() and re.match(r'Run_\d{8}_\d{9}', path.name):
                test_collection_runs.append(results_folder_name / path.name)
    return test_collection_runs

# this function creates a list of dictionary objects. Each dictionary object contains the collection name that the test belongs to, 
# the name of the test and the attempt. The function has a parameter that is an absolute root path which is a path object. 
# The function also has a parameter that is the path of the collection run relative to the absolute path.
# The function reads in the subdirectories of the collection run path and creates a list of all subdirectories which are the names of the tests.
# The function then reads in the subdirectories of each test and creates a list of all subdirectories which are the names of the attempts.
# The function then creates a list of dictionary objects. Each dictionary object contains the collection name that the test belongs to,
# the name of the test and the attempt. The function returns the list of dictionary objects. The function does not return any dictionary objects
# for tests that have no attempts. 
def get_test_attempts(root_path, collection_run_path):
    """Get a list of test attempts."""
    test_attempts = []
    abs_collection_run_path = root_path / collection_run_path
    for test_path in abs_collection_run_path.iterdir():
        if test_path.is_dir():
            for attempt_path in test_path.iterdir():
                if attempt_path.is_dir():
                    test_attempts.append({'collection_parent':collection_run_path.parent, 'collection_name': collection_run_path.name, 'test_name': test_path.name, 'attempt_number': attempt_path.name})
    return test_attempts

# This function gets a test attempt results. The function has a parameter that is the root path, and a dictionary object that contains the
# collection name, the test name, the attempt number. The function forms a path to the attempt directory and reads in the status and fail reason from
# the script file that is in the attempt directory. The script file name is in the form "<test_name>.script.log" where <test_name> is the name of the
# test. The function then reads the script file which is a text file and searches for the following lines:
# ```
# validate     = { PASS:2505, FAIL:0 }
# messages     = { INFO:4104, WARN:1, ERR:0, PENDING:0, INCONCLUSIVE:0, N/A:0 }
# ```
# It should also search for the line that contains the final verdict which is in the form: >>>> Final Verdict: PASS - "LL_CON_CEN_BV_04" <<<<
# The function creates a dictionary object that contains the parsed, PASS, FAIL, INFO, WARN, ERR, PENDING, INCONCLUSIVE, N/A values. It should also contain
# the "Final Verdict" line which is the single word status after the colon of the test.
def get_test_attempt_results(root_path, test_attempt):
    """Get the results for a test attempt."""
    test_attempt_path = root_path /test_attempt['collection_parent'] / test_attempt['collection_name'] / test_attempt['test_name'] / test_attempt['attempt_number']
    validate = None
    messages = None
    final_verdict = None
    # if file does not exist, return None
    if not (test_attempt_path / f'{test_attempt["test_name"]}.script.log').exists():
        return None
        
    with open(test_attempt_path / f'{test_attempt["test_name"]}.script.log') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('validate'):
                validate = line.split('=')[1].strip().strip('{}').split(',')
                validate = [int(x.split(':')[1]) for x in validate]
            if line.startswith('messages'):
                messages = line.split('=')[1].strip().strip('{}').split(',')
                messages = [int(x.split(':')[1]) for x in messages]
            # check if line contains final verdict (it will not start with it) and parse it if it does
            if line.find('Final Verdict') != -1:
                # the line may contain multiple colons so need to split on the last one
                final_verdict = line.rsplit(':', 1)[1].strip().split()[0]
                               
            
    if validate is None or messages is None or final_verdict is None:
        return None
    else:
        return {'collection_name': test_attempt['collection_parent'], 'collection_name': test_attempt['collection_name'], 'test_name': test_attempt['test_name'], 'attempt_number': test_attempt['attempt_number'],
            'final_verdict': final_verdict, 'PASS': validate[0], 'FAIL': validate[1], 'INFO': messages[0], 'WARN': messages[1], 'ERR': messages[2], 'PENDING': messages[3],
            'INCONCLUSIVE': messages[4], 'N/A': messages[5]}


# This function debugs a test attempt. The function has a parameter that is the root path. It loops through the run collection and prints out the run information before calling
# get_test_attempts. It then prints out the returned value and calls get_test_attempt_results for each attempt. It then prints out the returned value.
def debug_test_attempt(root_path):
    test_attempt_results_list = []
    """Debug a test attempt."""
    test_collection_runs = get_test_collection_runs(root_path)
    for collection_run in test_collection_runs:
        print(collection_run)
        test_attempts = get_test_attempts(root_path, collection_run)
        print(test_attempts)
        for test_attempt in test_attempts:
            if test_attempt_results := get_test_attempt_results(root_path, test_attempt):
                test_attempt_results_list.append(test_attempt_results)
                print(test_attempt_results_list[-1])
            else:
                print(f'Failed to get results for {test_attempt}')  
    return test_attempt_results_list

# This function loads a set of test attempt results and returns them in a list of dictionary objects. The function has a parameter that is the root path. It loops through the run collection 
# and calls get_test_attempts. Then once it has a list of test attempts it loops through the list and calls get_test_attempt_results for each attempt.
# Then once it has a list of test attempt results it returns the list.
def load_test_attempt_results(root_path):
    """Store test attempt results in a MongoDB collection."""
    test_attempt_results_list = []
    test_collection_runs = get_test_collection_runs(root_path)
    for collection_run in test_collection_runs:
        test_attempts = get_test_attempts(root_path, collection_run)
        for test_attempt in test_attempts:
            if test_attempt_results := get_test_attempt_results(root_path, test_attempt):
                test_attempt_results_list.append(test_attempt_results)
            else:
                print(f'Failed to get results for {test_attempt}')
    print(f'Total number of test attempt results: {len(test_attempt_results_list):,}')
    return test_attempt_results_list
    


# add the main function to call the debug_test_attempt function
if __name__ == '__main__':
    
    # # Initialize the MongoClient and connect to the database and collection
    # client = MongoClient('mongodb://localhost:27017/')
    # db = client.test_database
    # test_results_collection = db.test_results    
    
    # Create a connection to the MongoDB server
    client = MongoClient('mongodb://localhost:27017/')

    # Get a reference to your database
    db = client.test_harmony_database

    # Get a reference to your collection
    collection_name = "tdy"

    # Drop the collection if it exists (this will remove the collection and all documents in it)
    if collection_name in db.list_collection_names():
        collection = db[collection_name]
        collection.drop()

    # Create a new collection (this step is optional because MongoDB creates collections automatically when you insert documents)
    db.create_collection(collection_name)
    collection = db[collection_name]
    
    # Now you have a new, empty collection ready for use
    test_attempt_results_list=load_test_attempt_results(Path('/mnt/hgfs/Frontline/TDY'))
    
    # print the length of the total list of test attempt results properly formatted
    print(f'Total number of test attempt results: {len(test_attempt_results_list):,}')
    
    # Insert the list of dictionary objects as separate documents
    collection.insert_many(test_attempt_results_list)

    # Verify the insertion (optional)
    for doc in collection.find():
        print(doc)
    