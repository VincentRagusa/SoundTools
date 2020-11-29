from pydub import AudioSegment
from pydub.playback import play
from random import choice, uniform, randint, random
from pickle import load
from argparse import ArgumentParser

import sutils as SU


# Register Command Line Parameters
parser = ArgumentParser()
parser.add_argument('output', type=str, help="Outputs a sound file with the given name")
parser.add_argument('-f', '--frames', type=int, metavar="FRAMES", help="How many sound_frames will be used",default=1)
parser.add_argument('-l', '--layers', type=int, metavar="LAYERS", help="How many layers will be stacked",default=1)
parser.add_argument('-c', '--clipRange', type=float, nargs=2, metavar=("MIN","MAX"), help="Min and Max clip time in seconds.", default=[0.2,5])
parser.add_argument('-v', '--verbose', action='store_true', help="Turns on extra output.")
parser.add_argument('--serial', action='store_true', help="generates tracks serially (results in mixed groups).")


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
    if SU.doChance(0.2):
        cutoff = randint(300,10000)
        if args.verbose: print("\tEffect: Low-Pass ({}Hz)".format(cutoff))
        sound = sound.low_pass_filter(cutoff)
    if SU.doChance(0.2):
        cutoff = randint(300,10000)
        if args.verbose: print("\tEffect: High-Pass ({}Hz)".format(cutoff))
        sound = sound.high_pass_filter(cutoff)
    if SU.doChance(0.05):
        if args.verbose: print("\tEffect: Reverse")
        sound = sound.reverse()
    return sound


# ---------------------------------------------------------------------------------
def create_parallel():

    finalLayers = [AudioSegment.silent(duration=0) for _ in range(args.layers)]

    group = choice(includedGroups)
    print("Group Change ({}) at {}".format(group, SU.ms2hms(0)))
    lastGroupTime = 0

    panVars = [0.0 for _ in range(args.layers)]

    for f in range(args.frames):
        if SU.doChance(0.01) and max([len(layer) for layer in finalLayers])-lastGroupTime > 60000:
            oldGroup = group
            group = choice(includedGroups)
            while len(includedGroups) > 1 and group == oldGroup:
                group = choice(includedGroups)

            maxTrackLen = max([len(track) for track in finalLayers])
            for l in range(args.layers):
                padSize = 3000+maxTrackLen-len(finalLayers[l])
                if args.verbose: print("Adding pad of length {} to layer {}".format(padSize,l))
                pad = AudioSegment.silent(duration=padSize)
                finalLayers[l] += pad

            lastGroupTime = maxTrackLen+3000

            print("{} Group Change ({}) at {}".format(f, group, SU.ms2hms(lastGroupTime) ))

        if args.verbose: print("Frame {} Group {}".format(f,group))

        for l in range(args.layers):
            if args.verbose: print("Layer {}...".format(l))
            sound = loadClip(group)
            sound = layer_blends(sound, group)
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


def export_sound_parallel(export_args):
    master = AudioSegment.silent()

    layers = create_parallel()
    for layer in layers:
        master = layer.overlay(master)

    master = master.normalize(3)

    print("Saving {} to disk...".format(export_args))

    exportFormat = export_args.split(".")[-1]

    master.export(export_args,format=exportFormat)


# ---------------------------------------------------------------------------------
#generates a sequence of sound_frames sounds
def create_serial(sounds_frames):

    final = AudioSegment.silent(duration=0)

    group = choice(includedGroups)
    print("Group Change ({}) at {}".format(group, SU.ms2hms(len(final))))
    lastGroupTime = len(final)

    panVar = 0.0

    for x in range(sounds_frames):
        if SU.doChance(0.01) and len(final)-lastGroupTime > 60000:
            oldGroup = group
            group = choice(includedGroups)
            while len(includedGroups) > 1 and group == oldGroup:
                group = choice(includedGroups)
            print("{} Group Change ({}) at {}".format(x, group, SU.ms2hms(len(final)) ))
            final += AudioSegment.silent(duration=3000)
            lastGroupTime = len(final)

        if args.verbose: print("Frame {} Group {}".format(x,group))

        sound = loadClip(group)
        sound = layer_blends(sound, group)
        sound = sound.normalize(6)
        sound = add_effects(sound)

        #pad = AudioSegment.silent(duration=uniform(0,100))
        sound = sound.fade_in(200).fade_out(200)
        #sound = pad + sound + pad
        panVar = max(-1, min(1, panVar + uniform(-0.2,0.2)))
        sound = sound.pan(panVar)
        final += sound

        if args.verbose: print("--------------------------------")
    return final


#main method, called from the generate option
def export_sound_serial(export_args):
    master = AudioSegment.silent()

    for x in range(args.layers):
        print("Generating layer {} ...".format(x+1))
        #build sound from smaller parts
        layer = create_serial(args.frames)
        master = layer.overlay(master)

    master = master.normalize(3)

    print("Saving {} to disk...".format(export_args))
    exportFormat = export_args.split(".")[-1]
    master.export(export_args,format=exportFormat)
# ---------------------------------------------------------------------------------



if __name__ == "__main__":
    # Read command line parameters and choose action
    args = parser.parse_args()

    soundBank = load(open("cache.p", 'rb'))
    includedGroups = SU.parseConfig()

    if args.serial:
        export_sound_serial(args.output)
    else:
        export_sound_parallel(args.output)

    print("Done.")
