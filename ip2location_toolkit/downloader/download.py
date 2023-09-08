import os, sys, requests
from pathlib import Path
from tqdm import tqdm
from colorama import Fore
from zipfile import ZipFile
from ..exceptions import DataBaseNotFound, DownloadLimitExceeded, DownloadPermissionDenied
from ..validators import token_validator, db_code_validator, path_validator

def get_dir_or_create(path):
    """
    This function checks if the given path exists and if it does not, it creates it.
    @param path The path to check.
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_tmp_dir():
    """
    This function returns the path to the temporary directory.
    @return The path to the temporary directory.
    """
    full_path = os.path.join(os.path.dirname(__file__), 'tmp')
    return get_dir_or_create(full_path)

def get_downloaded_zip_path(file_code):
    tmp_path = get_tmp_dir()
    file_path  = '/'.join([tmp_path, "{filename}.zip".format(filename=file_code)])
    return file_path

def download_file(url, path):
    # TODO fix progress bar
    chunk_size = 8192
    with requests.get(url, stream=True) as r:
        if r.status_code == 404:
            raise DataBaseNotFound
        if r.text.startswith('THIS FILE CAN ONLY BE DOWNLOADED'):
            raise DownloadLimitExceeded
        if r.text == 'NO PERMISSION':
            raise DownloadPermissionDenied

        tqdm_bar = tqdm(unit='B', unit_scale=True, desc="   " + path.split('/')[-1], total=int(r.headers.get('content-length', 0)))
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                tqdm_bar.update(chunk_size)
                f.write(chunk)
    return path

def download_database(file_code, token=None):
    try:
        token_validator(token)
    except Exception as e:
        print('Failed to download database. {}'.format(e.message))
        return

    url = "https://www.ip2location.com/download?token={}&file={}".format(token, file_code)
    file_path = get_downloaded_zip_path(file_code)
    print('Downloading {}...'.format(Fore.BLUE + file_code + Fore.RESET))

    try:
        file = download_file(url, file_path)
    except Exception as e:
        print('   Error downloading {}. \n   {}'.format(Fore.RED + file_code + Fore.RESET, e.message))
        return

    print('   Downloaded {}.'.format( Fore.GREEN + file_code + Fore.RESET))
    return file

def unzip_db(file_path, output_path=None):
    try:
        with ZipFile(file_path, 'r') as zip_ref:
            to_extract = [f for f in zip_ref.namelist() if f.endswith('.BIN') or f.endswith('.CSV')]
            for f in to_extract:
                print('   Extracting {}...'.format(Fore.BLUE + f + Fore.RESET))
                zip_ref.extract(f, output_path)
    except Exception as e:
        print('   Error unzipping {}.'.format(Fore.RED + file_path.split('/')[-1] + Fore.RESET))
        raise e

    if not output_path:
        output_path = os.path.abspath(Path.cwd())

    print('   Extracted {} into {}'.format(Fore.GREEN + f + Fore.RESET, Fore.GREEN + output_path + Fore.RESET))
    return output_path + '/' + f

def download_extract_db(db_code, token=None, output_path=None):
    try :
        token_validator(token)
        db_code_validator(db_code)
        path_validator(output_path, required=False)
    except Exception as e:
        print('Failed to download database. {}'.format(e.message))
        return

    file_path = download_database(db_code, token)
    if not file_path:
        return
    output_file_path = unzip_db(file_path, output_path)
    return output_file_path