
from scicat_common import scicat_username_login
from scicat_ingestion import create_dataset, IngestionException
import os
from pathlib import Path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="SciCat Ingestor Mock",
        description="This application ingests a dataset",
        epilog="Refer to README.md to learn more"
    )

    parser.add_argument("-b", "--baseurl", required=True)
    parser.add_argument("-u", "--user")
    parser.add_argument("-p", "--password")
    parser.add_argument("-t", "--token")
    parser.add_argument("--path")
    args = parser.parse_args()
    
    base_url = args.baseurl
    user = args.user
    password = args.password
    token = args.token
    path_to_dataset = Path(args.path)

    if token is None:
        token = scicat_username_login(base_url, user, password)
    
    if not os.path.isfile(path_to_dataset / "transfer.yaml"):
        print("ERR: There's no 'transfer.yaml' to fill out metadata, aborting...")
        exit(-1)
    
    print("Ingesting dataset at {}... ".format(path_to_dataset), end="")
    try:
        dataset_id = create_dataset(path_to_dataset, base_url, token)[0]
    except (IngestionException) as e:
        print("Failed: '{}'".format(e))
        exit(-2)

    print("Done.")
    print("ID of dataset is '{}'".format(dataset_id))
