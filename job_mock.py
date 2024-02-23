import requests
from pathlib import Path
from typing import Union
from scicat_ingestion import create_dataset, dataset_check, IngestionException
from scicat_archival import create_job, forward_job, handle_job, ArchivalMockException
import yaml
import os

def scicat_login_with_user_pw(base_url: str, username: str, pw: str) -> Union[str, None]:
    # Create a client object.
    login_json = {
        'username': user,
        'password': pw,
        'rememberMe': True
    }
    r = requests.post(base_url + '/Users/login', json=login_json)
    if r.status_code == 200:
        response = r.json()
        if response is not None:    
            # return login token
            return response['id']
        else:
            print("ERR: invalid response from server")
            return None
    else:
        print("ERR: login request failed: ", r.status_code, r.reason)
        return None

def dataset_file_list_creator(path: Path) -> list[str]:
    sub_paths = [] # Collect all files in sub directories
    for root, dirs, files in os.walk(path):
        sub_paths += [os.path.join(root,i) for i in files if "transfer.yaml" not in i or not Path(root) == path]
        #print("AAAAA", root, path, Path(root) == path)
    return sub_paths


def ingest_and_archive_datasets_in_folder(dataset_src: Path, base_url: str, token: str):    
    for d in os.listdir(dataset_src):
        if not os.path.isfile(dataset_src / d / "transfer.yaml"):
            continue
        with open(dataset_src / d / "transfer.yaml", "r") as fd:
            transfer_config = yaml.safe_load(fd)
        
        file_paths = dataset_file_list_creator(dataset_src / d)
        #print(file_paths)
        
        # do the ingestion and archival steps here 
        # NOTE: while we could reuse the id we got in dataset creation for the job and dataset finalisation phases, 
        #   it is explicitly omitted in order to test the GET methods for finding the correct dataset and simulate 
        #   the behaviour that would happen normally
        print("Ingesting and archiving dataset at {}... ".format(d), end="")
        try:
            #dataset_check(base_url, token, dataset_src.resolve() / d)
            dataset_id, file_list = create_dataset(dataset_src / d, base_url, token, transfer_config, file_paths=file_paths)
            job_id = create_job(base_url, token, dataset_pid=dataset_id, dataset_files=file_list)
            datasets = forward_job(base_url, token, job_id)[1]
            handle_job(base_url, token, job_id, datasets)
        except (IngestionException, ArchivalMockException) as e:
            print("Failed: '{}'".format(e))
            continue
        print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="SciCat Job Creator/Handler",
        description="This application creates and handles jobs on SciCat in order to manipulate the state \
            of Datasets' archival",
        epilog="Refer to README.md to learn more"
    )

    parser.add_argument("-b", "--baseurl", required=True)
    parser.add_argument("-u", "--user")
    parser.add_argument("-p", "--password")
    parser.add_argument("-t", "--token")
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    
    base_url = args.baseurl
    user = args.user
    password = args.password
    token = args.token
    path_to_datasets = Path(args.path)

    if token is None:
        r = requests.post(base_url + "/Users/login", json={"username": "admin", "password": "2jf70TPNZsS"})
        if r.status_code == 200:
            token = r.json()['id']
        else:
            print("ERROR: cannot login with provided credentials and base url, reason: {} - {}".format(r.status_code,
                                                                                                        r.reason))
            exit(-1)

    ingest_and_archive_datasets_in_folder(path_to_datasets, base_url, token)
    
    print("Exiting.")