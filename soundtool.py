from pydub import AudioSegment
from pydub.playback import play
from pydub.silence import split_on_silence
from random import choice, uniform, randint, random
from pathlib import Path
from pickle import dump, load
from argparse import ArgumentParser

# Register Command Line Parameters
parser = ArgumentParser()
parser.add_argument('-f','--frames', type=int, metavar="FRAMES", help="How many sound_frames will be used",default=1)
parser.add_argument('-l','--layers', type=int, metavar="LAYERS", help="How many layers will be stacked",default=1)
parser.add_argument('-c','--create', type=str, metavar="FILENAME", help="Outputs a sound file with the given name")
parser.add_argument('-b','--buildCache', type=str, metavar="ROOTDIR", help="rebuilds the sound file cache from the given directory")
parser.add_argument('-s','--slice', type=str, nargs=3, metavar=("INPUT","OUTPUTDIR","THRESHOLD"), help="Slices an input file and stores the output in a directory")
parser.add_argument('--clipRange', type=float, nargs=2, metavar=("MIN","MAX"), help="Min and Max clip time in seconds.", default=[1,10])
parser.add_argument('-v','--verbose', action='store_true', help="Turns on extra output.")

#scans filesystem starting from root for directories containing .wav files
def buildCache(ROOT):
    print("Scanning Filesystem...")
    soundDirs = Path(ROOT).glob("*")
    soundDirs = list(map(str, soundDirs ))

    soundBank = {sd[len(ROOT):] : list(map(str, Path(sd).glob("*.wav") )) for sd in soundDirs }
    print("Caching {} sound files from {} directories...".format(sum([len(soundBank[k]) for k in soundBank]), len(soundBank)))
    dump(soundBank, open("cache.p", 'wb'))

    print("Generating config file...")
    with open("createSound.cfg", 'w') as configFile:
        for key in soundBank:
            configFile.write("+ {}\n".format(key))


def parseConfig():
    with open("createSound.cfg", 'r') as configFile:
        result = [line[1:].strip() for line in configFile if line[0] == '+']
        if not result:
            print("config error: no sound directories included.")
            exit(1)
        return result


# converts miliseconds (int) to hours minutes seconds (str)
def ms2hms(millis):
    seconds = millis // 1000
    minutes = 0
    while seconds >= 60:
        minutes += 1
        seconds -= 60
    hours = 0
    while minutes >= 60:
        hours += 1
        minutes -= 60
    return "{}h {}m {}s".format(hours, minutes, seconds)


# Returns 'True' with 'prob' probability
def doChance(prob):
    assert 0.0 <= prob <= 1.0
    return random() <= prob


# Loads a clip from 'group' and checks the length. If invalid, redraws.
def loadClip(group):
    result = AudioSegment.from_wav( choice(soundBank[group]) )
    while not args.clipRange[0]*1000 < len(result) < args.clipRange[1]*1000:
        result = AudioSegment.from_wav( choice(soundBank[group]) )
    return result


def layer_blends(sound, group):
    #layer blends
    layer_pool = randint(1,3)
    if layer_pool == 1:
        if args.verbose: print("\tLayer Mode: Raw")
    if layer_pool == 2:
        cutoff = randint(300,16000)
        if args.verbose: print("\tLayer Mode: High/Low Blend ({}Hz)".format(cutoff))
        sound2 = loadClip(group)
        sound = sound.low_pass_filter(cutoff)
        sound2 = sound2.high_pass_filter(cutoff)
        sound = sound.overlay(sound2)
    if layer_pool == 3:
        if args.verbose: print("\tLayer Mode: Overlay")
        sound2 = loadClip(group)
        sound = sound.overlay(sound2)
    return sound


def add_effects(sound):
    #effect sound clip
    if doChance(0.2):
        cutoff = randint(300,10000)
        if args.verbose: print("\tEffect: Low-Pass ({}Hz)".format(cutoff))
        sound = sound.low_pass_filter(cutoff)
    if doChance(0.2):
        cutoff = randint(300,10000)
        if args.verbose: print("\tEffect: High-Pass ({}Hz)".format(cutoff))
        sound = sound.high_pass_filter(cutoff)
    if doChance(0.05):
        if args.verbose: print("\tEffect: Reverse")
        sound = sound.reverse()
    return sound


def create_TEST():

    finalLayers = [AudioSegment.silent(duration=0) for _ in range(args.layers)]

    group = choice(includedGroups)
    print("Group Change ({}) at {}".format(group, ms2hms(0)))
    lastGroupTime = 0

    panVars = [0.0 for _ in range(args.layers)]

    for f in range(args.frames):
        if doChance(0.01) and max([len(layer) for layer in finalLayers])-lastGroupTime > 60000:
            oldGroup = group
            group = choice(includedGroups)
            while group == oldGroup:
                group = choice(includedGroups)

            maxTrackLen = max([len(track) for track in finalLayers])
            for l in range(args.layers):
                padSize = 3000+maxTrackLen-len(finalLayers[l])
                if args.verbose: print("Adding pad of length {} to layer {}".format(padSize,l))
                pad = AudioSegment.silent(duration=padSize)
                finalLayers[l] += pad

            lastGroupTime = maxTrackLen+3000

            print("{} Group Change ({}) at {}".format(f, group, ms2hms(lastGroupTime) ))

        if args.verbose: print("Frame {} Group {}".format(f,group))

        for l in range(args.layers):
            if args.verbose: print("Layer {}...".format(l))
            #grip sound clipV
            sound = loadClip(group)
            sound = layer_blends(sound, group)
            #gives sound headroom to prevent clipping
            sound = sound.normalize(6)
            sound = add_effects(sound)
            #pad = AudioSegment.silent(duration=uniform(0,100))
            sound = sound.fade_in(200).fade_out(200)
            #sound = pad + sound + pad
            sound = sound.pan(panVars[l])
            finalLayers[l] += sound

        panVars = [max(-1, min(1, pv + uniform(-0.2,0.2))) for pv in panVars]

        if args.verbose: print("--------------------------------")

    return finalLayers


def export_sound_TEST(export_args):
    master = AudioSegment.silent()

    layers = create_TEST()
    for layer in layers:
        master = layer.overlay(master)

    master = master.normalize(3)

    print("Saving {} to disk...".format(export_args))

    exportFormat = export_args.split(".")[-1]

    master.export(export_args,format=exportFormat)

#generates a sequence of sound_frames sounds
def create(sounds_frames):

    final = AudioSegment.silent(duration=0)

    group = choice(includedGroups)
    print("Group Change ({}) at {}".format(group, ms2hms(len(final))))
    lastGroupTime = len(final)

    panVar = 0.0

    for x in range(sounds_frames):
        if doChance(0.01) and len(final)-lastGroupTime > 60000:
            oldGroup = group
            group = choice(includedGroups)
            while group == oldGroup:
                group = choice(includedGroups)
            print("{} Group Change ({}) at {}".format(x, group, ms2hms(len(final)) ))
            final += AudioSegment.silent(duration=3000)
            lastGroupTime = len(final)

        if args.verbose: print("Frame {} Group {}".format(x,group))

        #grip sound clip
        sound = loadClip(group)

        #layer blends
        layer_pool = randint(1,3)
        if layer_pool == 1:
            if args.verbose: print("\tLayer Mode: Raw")
        if layer_pool == 2:
            cutoff = randint(300,16000)
            if args.verbose: print("\tLayer Mode: High/Low Blend ({}Hz)".format(cutoff))
            sound2 = loadClip(group)
            sound = sound.low_pass_filter(cutoff)
            sound2 = sound2.high_pass_filter(cutoff)
            sound = sound.overlay(sound2)
        if layer_pool == 3:
            if args.verbose: print("\tLayer Mode: Overlay")
            sound2 = loadClip(group)
            sound = sound.overlay(sound2)

        #gives sound headroom to prevent clipping
        sound = sound.normalize(6)

        #effect sound clip
        if doChance(0.2):
            cutoff = randint(300,10000)
            if args.verbose: print("\tEffect: Low-Pass ({}Hz)".format(cutoff))
            sound = sound.low_pass_filter(cutoff)
        if doChance(0.2):
            cutoff = randint(300,10000)
            if args.verbose: print("\tEffect: High-Pass ({}Hz)".format(cutoff))
            sound = sound.high_pass_filter(cutoff)
        if doChance(0.05):
            if args.verbose: print("\tEffect: Reverse")
            sound = sound.reverse()

        #append sound clip
        #pad = AudioSegment.silent(duration=uniform(0,100))
        sound = sound.fade_in(200).fade_out(200)
        #sound = pad + sound + pad
        panVar = max(-1, min(1, panVar + uniform(-0.2,0.2)))
        sound = sound.pan(panVar)
        final += sound

        if args.verbose: print("--------------------------------")
    return final


#main method, called from the generate option
def export_sound(export_args):
    master = AudioSegment.silent()

    for x in range(args.layers):
        print("Generating layer {} ...".format(x+1))
        #build sound from smaller parts
        layer = create(args.frames)
        master = layer.overlay(master)

    master = master.normalize(3)

    print("Saving {} to disk...".format(export_args))
    exportFormat = export_args.split(".")[-1]
    master.export(export_args,format=exportFormat)

# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)


def slice_clip(slice_args):
    sound = AudioSegment.from_mp3(slice_args[0])
    print("slicing chunks...")

    # set sound to mono
    sound = sound.set_channels(1)

    chunks = split_on_silence(sound,
        # must be silent for at least half a second
        min_silence_len=180,

        # consider it silent if quieter than -16 dBFS
        silence_thresh=int(slice_args[2])
    )
    chunkSizes = []
    # Process each chunk with your parameters
    for i, chunk in enumerate(chunks):

        # Normalize the entire chunk.
        normalized_chunk = match_target_amplitude(chunk, -20.0)


        # Export the audio chunk with new bitrate.
        if args.verbose:
            chunkSizes.append(len(chunk))
            print("Exporting chunk{0}.wav.".format(i))
            print("\tChunk Size: {}".format(ms2hms(len(chunk))))

        #if not args.clipRange[0]*1000 < len(chunk) < args.clipRange[1]*1000:
        #    if args.verbose: print("\tIgnoring Chunk.")
        #    continue
        normalized_chunk.export(
            slice_args[1]+"chunk{0}.wav".format(i),
            format = "wav"
        )
    if args.verbose:
        import matplotlib.pyplot as plt
        plt.hist(chunkSizes, bins=50)
        plt.show()

if __name__ == "__main__":
    # Read command line parameters and choose action
    args = parser.parse_args()

    if args.create:
        #load sound file library
        soundBank = load(open("cache.p", 'rb'))
        includedGroups = parseConfig()
        export_sound_TEST(args.create)
    elif args.buildCache:
        buildCache(args.buildCache)
    elif args.slice:
        slice_clip(args.slice)


    print("Done.")
