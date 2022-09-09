RELEASES_QUERY = '''
query($owner:String!, $repo:String!, $releasesCursor:String) {
  repository(owner: $owner, name: $repo) {
    releases(first:100, after:$releasesCursor) {
      pageInfo { endCursor hasNextPage }
      nodes {
        isLatest
        tagName
      }
    }
  }
}
'''

ARTIFACTS_QUERY = '''
query($owner:String!, $repo:String!, $tagName:String!, $releaseAssetsCursor:String) {
  repository(owner: $owner, name: $repo) {
    release(tagName: $tagName) {
      releaseAssets(first: 100, after:$releaseAssetsCursor) {
        pageInfo { endCursor hasNextPage }
        nodes {
          name
          downloadUrl
        }
      }
    }
  }
}
'''
