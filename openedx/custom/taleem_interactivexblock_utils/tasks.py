from celery import task
import zipfile
import os
from django.conf import settings
from path import Path as path
import logging
from django.core.files.storage import  get_storage_class, default_storage
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey
from openedx.custom.taleem_interactivexblock_utils.models import H5PExtraction
import shutil
import subprocess
from django.utils import timezone
from xblock.fields import DateTime
import uuid
FILE_READ_CHUNK = 1024  # bytes





def find_relative_file_path(filename, extract_folder_path, storage):
        return os.path.relpath(find_file_path(filename, extract_folder_path,storage ), extract_folder_path)


def find_file_path(filename, extract_folder_path, storage):
    path = get_file_path(filename, extract_folder_path, storage)
    if path is None:
        raise Exception(
            "Invalid package: could not find '{}' file".format(filename)
        )
    return path




def get_file_path(filename, root, storage):
    root = os.path.join(root, '')
    subfolders, files = storage.listdir(root)
    for f in files:
        if f == filename:
            return os.path.join(root, filename)
    for subfolder in subfolders:
        path = get_file_path(filename, os.path.join(root, subfolder), storage)
        if path is not None:
            return path
    for file in files:
        if os.path.isdir(file) or file.endswith('/'):
            path = get_file_path(filename, os.path.join(root, file),storage)
            if path is not None:
                return path
    return None


def recursive_delete(storage, root):
    root = os.path.join(root, '')
    directories, files = storage.listdir(root)
    for directory in directories:
        recursive_delete(storage, os.path.join(root, directory))
    for file in files:
        if os.path.isdir(file) or file.endswith('/'):
            recursive_delete(storage, os.path.join(root, file))
    for f in files:
        storage.delete(os.path.join(root, f))




def h5p_clean_storage(extract_folder_base_path):
    storage_class = settings.XBLOCK_SETTINGS['H5PXBlock'].get("STORAGE_CLASS", None)
    storage_root = settings.XBLOCK_SETTINGS['H5PXBlock'].get("STORAGE_ROOT", None)
    storage = get_storage_class(storage_class)(
            bucket_name=storage_root,
            querystring_auth=False,
        )
    directories, files = storage.listdir(os.path.join(extract_folder_base_path, ''))
    if directories or files:
        logging.info(
            'Removing previously unzipped "%s"', extract_folder_base_path
        )
        recursive_delete(storage, extract_folder_base_path)




def update_failed_extraction_status(block_id, msg):
    h5p_extraction = H5PExtraction.objects.filter(block_id=block_id).first()
    h5p_extraction.status = 'failed'
    h5p_extraction.error_message = msg
    h5p_extraction.save()



@task()
def task_extract_package(**kwargs):
    logging.info('h5p extraction started')
    package_file_path = kwargs['package_file_path']
    extract_folder_path = ''
    storage = default_storage
    root_path = ''
    filename = kwargs['filename']
    storage_class = kwargs['storage_class']
    storage_root = kwargs['storage_root']
    block_id = kwargs['block_id']
    block_id = str(block_id)
    user_id = kwargs['user_id']
    bucket_name = storage_root
    usage_key = UsageKey.from_string(block_id)
    block = modulestore().get_item(usage_key, depth=None)

    try:

        data_root = path(settings.GITHUB_REPO_ROOT)
        subdir = data_root / str(uuid.uuid4())
        temp_filepath = subdir / filename
        temp_download_dir_list = temp_filepath.split('/')[:-1]
        temp_download_dir = "/".join(temp_download_dir_list)
        if not subdir.isdir():
            os.makedirs(subdir)

        if storage_class and storage_root:
                storage = get_storage_class(storage_class)(
                bucket_name=storage_root,
                querystring_auth=False,
            )


        command = "mc cp " + settings.MC_CLIENT_CEPH_ALIAS + "/" + bucket_name + "/" + package_file_path + " " + str(temp_filepath)
        logging.info('downloading file')    
        logging.info(command)
        process = subprocess.Popen(command , stdout=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        exit_code = process.wait()
        if exit_code !=0:
            msg = 'some error occured while downloading file'
            logging.info(msg)
            update_failed_extraction_status(block_id, msg)
            return


        logging.info('generating sha1')
        with open(temp_filepath, 'rb') as package_file:
            block.package_meta["sha1"] = block.get_sha1(package_file)
            block.package_meta["name"] = package_file.name
            block.package_meta["last_updated"] = timezone.now().strftime(
                DateTime.DATETIME_FORMAT
            )
            block.package_meta["size"] = package_file.seek(0, 2)
            package_file.seek(0)
        
        with zipfile.ZipFile(temp_filepath, "r") as h5p_zipfile:
            zipinfos = h5p_zipfile.infolist()
            root_path = None
            root_depth = -1
            # Find root folder which contains h5p.json
            for zipinfo in zipinfos:
                if os.path.basename(zipinfo.filename) == "h5p.json":
                    depth = len(os.path.split(zipinfo.filename))
                    if depth < root_depth or root_depth < 0:
                        root_path = os.path.dirname(zipinfo.filename)
                        root_depth = depth

            if root_path is None:
                msg = "Could not find 'h5p.json' file in the h5p package"
                logging.info(msg)
                update_failed_extraction_status(block_id, msg)
                return
        
        extract_folder_path = settings.XBLOCK_SETTINGS['H5PXBlock']['LOCATION'] + "/" + block.location.block_id + "/" + block.package_meta["sha1"]

        extract_folder_base_path_list = extract_folder_path.split('/')[:-1]
        extract_folder_base_path = "/".join(extract_folder_base_path_list)
        
        

        extracted_folder_path = "/tmp/" + extract_folder_path
        extracted_folder_path_list = extracted_folder_path.split('/')
        base_extracted_folder_path = "/".join(extracted_folder_path_list[:-1])

        if not path(extracted_folder_path).isdir():
            os.makedirs(extracted_folder_path)
        else:
            shutil.rmtree(base_extracted_folder_path)
            os.makedirs(extracted_folder_path)


        command = 'unzip ' + temp_filepath + " -d " + extracted_folder_path
        logging.info('extracting file')
        logging.info(command)
        process = subprocess.Popen(command , stdout=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        exit_code = process.wait()
        if exit_code !=0:
            msg = "some error occured while extracting folder to server"
            logging.info(msg)
            update_failed_extraction_status(block_id, msg)
            return 

        custom_extract_folder_base_path = os.path.join(settings.XBLOCK_SETTINGS['H5PXBlock']['LOCATION'], block.location.block_id)
        logging.info('clean previous data')
        h5p_clean_storage(custom_extract_folder_base_path)

        upload_command = 'mc cp --recursive ' + extracted_folder_path + " " + settings.MC_CLIENT_CEPH_ALIAS + "/" + bucket_name + "/" + extract_folder_path
        logging.info('uploading to ceph')
        logging.info(upload_command)
        process = subprocess.Popen(upload_command , stdout=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        exit_code = process.wait()
        if exit_code !=0:
            msg = "some error occured while uploading extracted folder"
            logging.info(msg)
            update_failed_extraction_status(block_id, msg)
            return 
        
        index_page_path = find_relative_file_path('h5p.json', extract_folder_path, storage)
        #block.update_package_fields()
        modulestore().update_item(block, user_id)
        #block.save()
        h5p_extraction = H5PExtraction.objects.filter(block_id=block_id).first()
        h5p_extraction.status = 'completed'
        h5p_extraction.index_page_path = str(index_page_path)
        h5p_extraction.save()
        shutil.rmtree(temp_download_dir)
        shutil.rmtree(base_extracted_folder_path)
        storage.delete(package_file_path)
    except Exception as e:
        logging.info('some error occured while extracing H5P package')
        logging.info(e)
        update_failed_extraction_status(block_id, str(e))
