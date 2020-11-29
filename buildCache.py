from argparse import ArgumentParser
from pathlib import Path
from pickle import dump


parser = ArgumentParser()
parser.add_argument('rootDir', type=str, help="rebuilds the sound file cache from the given directory")
parser.add_argument('-v','--verbose', action='store_true', help="Turns on extra output.")


#scans filesystem starting from root for directories containing .wav files
def buildCache(ROOT):
    print("Scanning Filesystem...")
    soundDirs = Path(ROOT).glob("*")
    soundDirs = list(map(str, soundDirs ))
    soundBank = {sd[len(ROOT):] : list(map(str, Path(sd).glob("*.wav") )) for sd in soundDirs }

    print("Caching {} sound files from {} directories...".format(sum([len(soundBank[k]) for k in soundBank]), len(soundBank)))
    dump(soundBank, open("cache.p", 'wb'))

    print("Generating groups config file...")
    with open("groups.cfg", 'w') as configFile:
        for key in soundBank:
            configFile.write("+ {}\n".format(key))


if __name__ == "__main__":
    args = parser.parse_args()

    buildCache(args.rootDir)

    print("Done.")
