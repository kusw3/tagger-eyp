#!/usr/bin/env python
from __future__ import print_function

"""
github release bot for puppet modules
"""

import os
import sys
import json
import argparse
from github import Github
from configparser import SafeConfigParser
from distutils.version import LooseVersion

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if __name__ == '__main__':

    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = './tagger.config'

    config = SafeConfigParser()
    config.read(config_file)

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
        repo_pattern = ''

    try:
        message = config.get('github', 'message').strip('"').strip()
    except:
        message = ''

    try:
        skip_forked_repos = config.getboolean('github', 'skip-forked-repos')
    except:
        skip_forked_repos = False

    try:
        debug = config.getboolean('github', 'debug')
    except:
        debug = False

    try:
        update_description = config.getboolean('github', 'update-description')
    except:
        update_description = True

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
                if debug:
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
                eprint("ERROR: retrieving metadata for {}: {}".format(repo.name,str(e)))
                continue

            # releases
            try:
                latest_release = '0.0.0'
                for rel in repo.get_releases():
                    if LooseVersion(latest_release) < LooseVersion(rel.title):
                        latest_release = rel.title
            except:
                eprint("ERROR: retrieving releases for {}".format(repo.name))
                continue

            if metadata['version'] != latest_release:
                # Create a new release as metadata version
                repo.create_git_release(tag=metadata['version'],name=metadata['version'],message=message)
                if debug:
                    print("Updating {} - Latest version: {} - Was: {}".format(repo.name, metadata['version'], latest_release))
            else:
                if debug:
                    print("No need to update {}".format(repo.name))

            # update repo title
            if update_description:
                if metadata['summary']:
                    repo.edit(description=metadata['version'])
