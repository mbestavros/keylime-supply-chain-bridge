import os
import sys

from .constants import github_constants
from githubgql import githubgql

def fetch_links_from_github(owner, repo, token):
    # Pagination cursors needed for API requests
    releases_cursors = {"releasesCursor": ["repository", "releases"]}
    artifacts_cursors = {"releaseAssetsCursor": ["repository", "release", "releaseAssets"]}

    # Fetch all releases from provided repo and find latest
    try:
        releases_result = githubgql.graphql(github_constants.RELEASES_QUERY, token=token, cursors=releases_cursors, owner=owner, repo=repo)
    except githubgql.TokenError as e:
        print(e.error)
        sys.exit(0)

    latest_tag_name = None
    for release in releases_result["repository"]["releases"]["nodes"]:
        if release["isLatest"] == True:
            latest_tag_name = release["tagName"]

    # Fetch all asset URLs from the latest release
    try:
        artifacts_result = githubgql.graphql(github_constants.ARTIFACTS_QUERY, token=token, cursors=artifacts_cursors, owner=owner, repo=repo, tagName=latest_tag_name)
    except githubgql.TokenError as e:
        print(e.error)
        sys.exit(0)

    # Organize URLs into understandable dictionaries
    artifacts_formatted = {}
    link_urls = {}
    for asset in artifacts_result["repository"]["release"]["releaseAssets"]["nodes"]:
        root, extension = os.path.splitext(asset["name"])
        url = asset["downloadUrl"]
        if extension == ".link":
            # Needed to get the base step name from a link file's path
            link_urls[root.split(".")[0]] = url
        else:
            if root not in artifacts_formatted.keys():
                artifacts_formatted[root] = {}
            match extension:
                case ".sig":
                    artifacts_formatted[root]["sig"] = url
                case ".crt":
                    artifacts_formatted[root]["crt"] = url
                case _:
                    artifacts_formatted[root]["artifact"] = url

    return artifacts_formatted, link_urls
