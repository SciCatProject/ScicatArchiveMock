from scicat_common import scicat_username_login, scicat_get_dataset_files, ScicatException
from scicat_archival import create_job, ArchivalMockException

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
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--job-type", required=True)
    args = parser.parse_args()
    
    base_url = args.baseurl
    user = args.user
    password = args.password
    token = args.token
    dataset_id = args.dataset_id
    job_type = args.job_type

    if token is None:
        token = scicat_username_login(base_url, user, password)

    if not (job_type == 'archival' or job_type == 'retrieval'):
        print("ERR: invalid job type")
        exit(-1)
    
    retrieval = (job_type == 'retrieval')
    
    try:
        dataset_files = scicat_get_dataset_files(base_url, token, dataset_id)
        job_id = create_job(base_url, token, retrieval, dataset_id, dataset_files)
    except (ScicatException, ArchivalMockException) as e:
        print("Can't create job: {}".format(e))
        exit(-2)
    print("Job created: {}".format(job_id))