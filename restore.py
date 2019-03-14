#!/usr/bin/env python3

# -*- coding: utf-8 -*-
#
# Author: Alberto Planas <aplanas@suse.com>
#
# Copyright 2019 SUSE LINUX GmbH, Nuernberg, Germany.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import argparse
import datetime
import os
import time
import urllib.parse


def get_list_of_files(directory):
    for (dirpath, dirnames, filenames) in os.walk(directory):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def read_polipo_cache(file_):
    """Return the content of a polipo cache file."""
    headers = {}
    with open(file_, 'rb') as f:
        for line in f.readlines():
            line = line.decode('utf-8').strip()
            # Read until we find an empty line
            if not line:
                break
            key_value = line.split(':', 1)
            if len(key_value) == 1:
                key, value = key_value[0], ''
            else:
                key, value = key_value
            headers[key.strip()] = value.strip()

        offset = int(headers.get('X-Polipo-Body-Offset', 0))
        f.seek(offset)
        content = f.read()

    url = headers['X-Polipo-Location']

    if 'X-Polipo-Access' in headers:
        date = headers['X-Polipo-Access']
    else:
        date = headers['Date']
    date = datetime.datetime.strptime(date, '%a, %d %b %Y %X %Z')

    return (url, date, content)


def store_repo(repo, url, date, content):
    """Store a file in the repository."""
    path = urllib.parse.urlparse(url).path
    full_name = os.path.join(repo, os.path.relpath(path, os.path.sep))
    path = os.path.dirname(full_name)

    if not os.path.exists(path):
        os.makedirs(path)

    with open(full_name, 'wb') as f:
        f.write(content)

    time_secs = time.mktime(date.timetuple())
    os.utime(full_name, (time_secs, time_secs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Rebuild a repository from a polipo proxy cache')
    parser.add_argument('cache', help='Polipo proxy cache directory')
    parser.add_argument('repo', help='Repository directory')

    args = parser.parse_args()
    for file_ in get_list_of_files(args.cache):
        (url, date, content) = read_polipo_cache(file_)
        store_repo(args.repo, url, date, content)
