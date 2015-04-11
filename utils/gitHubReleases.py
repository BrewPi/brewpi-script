import urllib2
import simplejson as json
import os

class gitHubReleases:
    def __init__(self, url):
        self.url = url
        self.releases = []
        self.update()

    def download(self, url, path):
        # Open the url
        try:
            f = urllib2.urlopen(url)
            print "downloading " + url

            # Open our local file for writing
            fileName = os.path.join(path, os.path.basename(url))
            with open(fileName, "wb") as localFile:
                localFile.write(f.read())
            return os.path.abspath(fileName)

        #handle errors
        except urllib2.HTTPError, e:
            print "HTTP Error:", e.code, url
        except urllib2.URLError, e:
            print "URL Error:", e.reason, url
        return None

    def update(self):
        self.releases = json.load(urllib2.urlopen(self.url + "/releases"))

    # writes .bin in release tagged with tag to directory
    # defaults to ./downloads/tag_name/ as download location
    def getBin(self, tag, wordsInFileName, path = None):
        try:
            match = (release for release in self.releases if release["tag_name"] == tag).next()
        except StopIteration:
            print "tag '{0}' not found".format(tag)
            return None
        downloadUrl = None

        AllUrls = (asset["browser_download_url"] for asset in match["assets"])

        for url in  AllUrls:
            if all(x in url for x in wordsInFileName):
                downloadUrl = url

        if not downloadUrl:
            print "Could not find download in release {0} and words in file name: {1}".format(tag, str(wordsInFileName))
            return None

        if path == None:
            path = os.path.join(os.path.dirname(__file__), "downloads")
            
        downloadDir = os.path.join(os.path.abspath(path), tag)
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)

        fileName = self.download(downloadUrl, downloadDir)
        return fileName

    def getLatestTag(self):
        return self.releases[0]["tag_name"]

    def getTags(self):
        return self.releases[0]["tag_name"]

if __name__ == "__main__":
    # test code
    releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")
    latest = releases.getLatestTag()
    print "Latest tag: " + latest
    print "Downloading binary for latest tag"
    localFileName = releases.getBin(latest, ["spark-core", "bin"])
    if localFileName:
        print "Latest binary downloaded to " + localFileName


