#!/usr/bin/env python

from __future__ import print_function

"""
Script to tag a release on each eyp module in NTTCMS repos
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
        GH_TOKEN = config.get('github', 'token')
    except:
        sys.exit("ERROR: github token is mandatory")

    try:
        repo_pattern = config.get('github', 'repo-pattern')
    except:
        repo_pattern="eyp-"

    try:
        gh_username = config.get('github', 'username')
    except:
        gh_username = "NTTCom-MS"

    try:
        skip_forked_repos = config.getboolean('github', 'skip-forked-repos')
    except:
        skip_forked_repos=False

    g = Github(GH_TOKEN)

    for repo in g.get_user(gh_username).get_repos():
        if repo_pattern in repo.name:

            if skip_forked_repos and repo.fork:
                print("skipping forked repo: {}".format(repo.name))
                continue

            try:
                metadata = json.loads(repo.get_contents("metadata.json").decoded_content)
            except:
                print("ERROR: retrieving metadata for {}".format(repo.name))
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
