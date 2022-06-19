import json
import os
import requests
import shutil
import tempfile
import urllib

CACHE_FILE = 'cache.txt'

def readFromCache():
    """read last downloaded album & track from the cache file"""
    with open(CACHE_FILE, 'r') as fp:
        cacheInfo = fp.read()
    words = cacheInfo.strip().split(' ')
    return (int(words[0]), int(words[1]))

def writeToCache(albumID, trackNum):
    """write last downloaded album & track to the cache file"""
    with open(CACHE_FILE, 'w') as fp:
        fp.write('{} {}'.format(albumID, trackNum))


def removeUnsupportedSymbols(filename):
    """remove unsupported symbols from the filename"""
    for symbol in [':', '?']:
        filename = filename.replace(symbol, '')

    for symbol in ['/']:
        filename = filename.replace(symbol, ' ')

    return filename


if __name__ == "__main__":
    # get path to save file to from user
    downloadBasePath = input('Download base path [./]: ') or "./"

    # get information about last downloaded album & track
    try:
        (lastAlbum, lastTrack) = readFromCache()
    # set default values if cache file doesn't exist
    except FileNotFoundError:
        (lastAlbum, lastTrack) = (0, 0)

    MAX_ALBUM_ID = 2000
    # iterate through albums IDs from lastAlbum-MAX_ALBUM_ID
    for curAlbum in range(lastAlbum, MAX_ALBUM_ID):
        # get json info about album
        resp = requests.get(
            'https://www.epidemicsound.com/json/albums/{}/'.format(curAlbum))

        # check validity of album with specified ID.
        # if album doesn't exist, save info about last album to cache file,
        # and make next iteration
        if len(resp.json()['entities']['albums']) == 0:
            writeToCache(curAlbum, 0)
            continue

        albumInfoJSON = resp.json()['entities']['albums'][str(curAlbum)]

        # not every album has information about its music genres, for some reason
        if len(albumInfoJSON['categories']) == 0:
            folderName = '{}'.format(albumInfoJSON['title'])
        # if there are some genres, take the first
        else:
            folderName = '{} [{}]'.format(
                albumInfoJSON['title'], albumInfoJSON['categories'][0]['name'])

        print('{}:'.format(folderName))

        # remove unsupported symbols from folder name
        folderName = removeUnsupportedSymbols(folderName)

        # make folder with the album name
        try:
            os.makedirs(downloadBasePath + folderName)
        except FileExistsError:
            pass

        curTrack = 0

        # iterate through album's tracks
        for track in resp.json()['entities']['tracks'].values():
            # skip the track if it's already downloaded
            if curAlbum == lastAlbum and curTrack < lastTrack:
                curTrack += 1
                continue

            # make temporary file to store downloaded mp3-file
            fd, tmpFileName = tempfile.mkstemp()

            trackUrl = track['stems']['full']['lqMp3Url']
            if len(track['creatives']['mainArtists']) == 0:
                trackAuthor = 'Unknown'
            else:
                trackAuthor = track['creatives']['mainArtists'][0]['name']

            trackName = removeUnsupportedSymbols(track['title'])
            finalFileName = downloadBasePath + \
                '{}/{} - {}.mp3'.format(folderName, trackAuthor, trackName)

            # download mp3-file, and store it into temporary file
            urllib.request.urlretrieve(trackUrl, tmpFileName)
            # then rename file and move it to final directory
            os.close(fd)
            shutil.move(tmpFileName, finalFileName)

            writeToCache(curAlbum, curTrack)
            curTrack += 1

            print('{} - {}'.format(trackAuthor, trackName))

        print(' ')
