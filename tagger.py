#!/usr/bin/env python

from __future__ import print_function

"""
Script to tag a releases
"""

import os
import sys
import json
import argparse
from github import Github
from configparser import SafeConfigParser
from distutils.version import LooseVersion

if __name__ == '__main__':

    try:
        basedir = sys.argv[1]
    except IndexError:
        basedir = '.'

    config = SafeConfigParser()
    config.read(basedir+'/tagger.config')

    try:
        GH_TOKEN = config.get('github', 'token').strip('"').strip()
    except:
        sys.exit("ERROR: PAT is mandatory")

    try:
        gh_username = config.get('github', 'username').strip('"').strip()
    except:
        sys.exit("ERROR: github username is mandatory")

    try:
        repo_pattern = config.get('github', 'repo-pattern').strip('"').strip()
    except:
        repo_pattern=""

    try:
        skip_forked_repos = config.getboolean('github', 'skip-forked-repos')
    except:
        skip_forked_repos=False

    try:
        debug = config.getboolean('github', 'debug')
    except:
        debug=False

    if debug:
        print("== config ==")
        print("username: "+gh_username)
        print("repo_pattern: "+repo_pattern)
        print("skip_forked_repos: "+str(skip_forked_repos))

    g = Github(GH_TOKEN)

    for repo in g.get_user(gh_username).get_repos():
        if repo_pattern in repo.name:

            if debug:
                print("considering: "+repo.name+" - is fork? "+str(repo.fork))

            if skip_forked_repos and repo.fork:
                print("skipping forked repo: {}".format(repo.name))
                continue

            try:
                metadata_json = repo.get_contents("metadata.json").decoded_content
                if type(metadata_json) is bytes:
                    metadata_json_str = metadata_json.decode("utf-8")
                elif type(metadata_json) is str:
                    metadata_json_str = metadata_json

                metadata = json.loads(metadata_json_str)
            except Exception as e:
                print("ERROR: retrieving metadata for {}: {}".format(repo.name,str(e)))
                continue

            try:
                latest_release = '0.0.0'
                for rel in repo.get_releases():
                    if LooseVersion(latest_release) < LooseVersion(rel.title):
                        latest_release = rel.title
            except:
                print("ERROR: retrieving releases for {}".format(repo.name))
                continue

            if metadata['version'] != latest_release:
                # Create a new release as metadata version
                print("{} not updated. Metadata version: {} - Release: {}".format(repo.name, metadata['version'], latest_release))
                repo.create_git_release(tag=metadata['version'],name=metadata['version'],message='NTTCMS EYP Tagger was here')
                print("!! {} relased to latest version: {}".format(repo.name, metadata['version']))
            else:
                if debug:
                    print("No need to update {}".format(repo.name))
