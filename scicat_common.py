import requests
import urllib

class ScicatException(Exception):
    pass

def check_request_response(r: requests.Response, msg: str) -> None:
    if not r.status_code == 200:
        raise ScicatException("{}: {} - {}".format(msg, r.status_code, r.reason))

def scicat_username_login(base_url: str, username: str, password: str):
    r = requests.post(base_url + "/Users/login", json={"username": "admin", "password": "2jf70TPNZsS"})
    if not r.status_code == 200:
        raise ScicatException("ERROR: cannot login with provided credentials and base url, reason: {} - {}".format(
            r.status_code, r.reason))
    token = r.json().get('id')
    if token is None:
        raise ScicatException("Invalid token response from Scicat")
    return token

def scicat_get_dataset_files(base_url: str, token: str, dataset_id: str):
    access_token = {'access_token': token}
    r = requests.get(base_url + "/Datasets/"+urllib.parse.quote(dataset_id, safe=''), params=access_token | 
                     {"filter": '{"include": [{"relation": "origdatablocks"}]}'})
    check_request_response(r, "can't retrieve dataset with the given id and current user")
    dataset = r.json()
    orig_datablocks = dataset.get('origdatablocks')
    if orig_datablocks is None:
        return [] # let's assume there are no orig. datablocks attached in this case
    if not isinstance(orig_datablocks, list): raise ScicatException("origdatablocks is not a list")
    dataset_files: list[str] = []
    for orig_datablock in orig_datablocks:
        file_list = orig_datablock.get('dataFileList')
        if file_list is None:
            continue # let's assume datablock is empty
        if not isinstance(file_list, list): raise ScicatException("dataFileList is not a list")
        for file in file_list:
            file_path = file.get('path')
            if isinstance(file_path, str):
                dataset_files.append(file_path)
            else:
                if file_path is not None:
                    raise ScicatException("invalid return for file_path: {}".format(file_path))
    
    return dataset_files