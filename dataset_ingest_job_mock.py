from pathlib import Path
from scicat_common import scicat_username_login
from scicat_ingestion import create_dataset, dataset_check, IngestionException
from scicat_archival import create_job, forward_job, handle_archive_job, ArchivalMockException
import os

def ingest_and_archive_datasets_in_folder(dataset_src: Path, base_url: str, token: str, dataset_check: bool):    
    for d in os.listdir(dataset_src):
        if not os.path.isfile(dataset_src / d / "transfer.yaml"):
            continue
        
        # do the ingestion and archival steps here 
        # NOTE: while we could reuse the id we got in dataset creation for the job and dataset finalisation phases, 
        #   it is explicitly omitted in order to test the GET methods for finding the correct dataset and simulate 
        #   the behaviour that would happen normally
        print("Ingesting and archiving dataset at {}... ".format(d), end="")
        try:
            if dataset_check: dataset_check(base_url, token, dataset_src.resolve() / d)
            dataset_id, file_list = create_dataset(dataset_src / d, base_url, token)
            job_id = create_job(base_url, token, dataset_pid=dataset_id, dataset_files=file_list)
            datasets = forward_job(base_url, token, job_id)
            handle_archive_job(base_url, token, job_id, datasets)
        except (IngestionException, ArchivalMockException) as e:
            print("Failed: '{}'".format(e))
            continue
        print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="SciCat Job Creator/Handler",
        description="This application ingests datasets in a folder, creates archival jobs for them and handles said \
              jobs on SciCat in order to test its API",
        epilog="Refer to README.md to learn more"
    )

    parser.add_argument("-b", "--baseurl", required=True)
    parser.add_argument("-u", "--user")
    parser.add_argument("-p", "--password")
    parser.add_argument("-t", "--token")
    parser.add_argument("--path", required=True)
    parser.add_argument("--check-dataset-duplication", action='store_true')
    args = parser.parse_args()
    
    base_url = args.baseurl
    user = args.user
    password = args.password
    token = args.token
    path_to_datasets = Path(args.path)
    dataset_duplication_check = args.check_dataset_duplication

    if token is None:
        token = scicat_username_login(base_url, user, password)

    ingest_and_archive_datasets_in_folder(path_to_datasets, base_url, token, dataset_duplication_check)
    
    print("Exiting.")