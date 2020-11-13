import papermill as pm
import shutil
from pathlib import Path

import os
import warnings
import argparse

import glob
from google.cloud import storage

warnings.filterwarnings('ignore')

def download_data(bucket_name, gcs_path, local_path):
    bucket = storage.Client().bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(local_path)

def upload_data(bucket_name, gcs_path, local_path):
    bucket = storage.Client().bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)
    
def get_bucket_path(gcs_uri):
    if not gcs_uri.startswith('gs://'):
        raise Exception('{} does not start with gs://'.format(gcs_uri))
    no_gs_uri = gcs_uri[len('gs://'):]
    first_slash_index = no_gs_uri.find('/')
    bucket_name = no_gs_uri[:first_slash_index]
    gcs_path = no_gs_uri[first_slash_index + 1:]
    return bucket_name, gcs_path

def upload_local_directory_to_gcs(local_path, bucket_name, gcs_path):
    bucket = storage.Client().bucket(bucket_name)
    assert os.path.isdir(local_path)
    for local_file in glob.glob(local_path + '/**'):
        if not os.path.isfile(local_file):
            upload_local_directory_to_gcs(local_file, bucket, gcs_path + "/" + os.path.basename(local_file))
        else:
            remote_path = os.path.join(gcs_path, local_file[len(local_path):])
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gcs_data_path', action="store", required=True)
    parser.add_argument('--gcs_notebook_path', action="store", required=True)
    parser.add_argument('--gcs_model_path', action="store", required=True)

    arguments, others = parser.parse_known_args()
    # local_path = '/tmp/workspace/'
    local_path = '/tmp/inputs/'
    Path('/tmp/inputs/outputs/').mkdir(parents=True, exist_ok=True)
    
    archive_name = arguments.gcs_data_path.split("/")[-1]
    notebook_name = arguments.gcs_notebook_path.split("/")[-1]
    
    if "gs://" not in arguments.gcs_data_path:
        data_archive_path = arguments.gcs_data_path
        notebook_path = arguments.gcs_notebook_path
        
        shutil.copyfile(notebook_path, local_path+ notebook_name)
        shutil.copyfile(data_archive_path, local_path+ archive_name)
    else:
        print('Downloading the data...')
        data_bucket, data_path = get_bucket_path(arguments.gcs_data_path)
        download_data(data_bucket, data_path, local_path+ archive_name)        

        print('Downloading the notebook...')
        data_bucket, data_path = get_bucket_path(arguments.gcs_notebook_path)
        download_data(data_bucket, data_path, local_path+ notebook_name)        

    data_archive_path = local_path + arguments.gcs_data_path.split("/")[-1]
    notebook_path = local_path + arguments.gcs_notebook_path.split("/")[-1]
        
    shutil.unpack_archive(data_archive_path, "/tmp/inputs/files")
    os.chdir("/tmp/inputs/outputs")
    
    print('Training the model...')
    pm.execute_notebook(
       notebook_path,
       local_path + 'outputs/resulting_nb_' + notebook_path.split("/")[-1],
       parameters=dict(Alpha=0.6, ratio=0.1),
       log_output=False,
       report_mode=True
    )
    
    
    if "gs://" not in arguments.gcs_model_path:
        pass
    else:
        model_bucket, model_path = get_bucket_path(arguments.gcs_model_path)
        upload_local_directory_to_gcs( '/tmp/inputs/outputs/', model_bucket, model_path)
        
    print('Model was successfully uploaded.')
    