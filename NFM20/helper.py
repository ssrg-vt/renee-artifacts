#! /usr/bin/env python

import os
import re
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))
udir_path = os.path.dirname(dir_path)


def build_file_path(path, file_names):
    file_name_list = file_names.split(' ')
    result = ' '.join(list(map(lambda s: preprocess_path(s, path), file_name_list)))
    return result


def add_prefix(prefix, names):
    name_list = names.split(' ')
    result = ' '.join(list(map(lambda s: prefix + ' ' + s, name_list)))
    return result


def preprocess_path(path, d_path=dir_path):
    if path.startswith('..'):
        path = re.sub('\.\./', os.path.dirname(d_path) + '/', path)
    elif path.startswith('./'):
        path = re.sub('\./', d_path + '/', path)
    elif not path.startswith('/'):
        path = os.path.join(d_path, path)
    return path


def execute_command(cmd):
    out = subprocess.check_output(cmd, shell=True)
    return out


def write_file(file_path, data):
    with open(file_path, 'w+') as f:
        f.write(data)



