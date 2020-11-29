from pydub import AudioSegment
from pydub.silence import split_on_silence
from argparse import ArgumentParser

import sutils as SU

parser = ArgumentParser()
parser.add_argument('input', type=str, help="sound file to slice")
parser.add_argument('outputDir', type=str, help="directory to export slices to")
parser.add_argument('-m','--minSilenceLen', type=int, help="minimum length of silence required to slice", default=180)
parser.add_argument('-t','--silenceThreshold', type=int, help="threshold (dB) that determines what \"silence\" is", default=-40)
parser.add_argument('-v','--verbose', action='store_true', help="Turns on extra output.")


def slice_clip(inFile, outDir, minSilence, threshold, verbose):
    print("Loading input file...")
    sound = AudioSegment.from_mp3(inFile)

    print("Setting Channels to mono...")
    channels = sound.split_to_mono()

    for c, channel in enumerate(channels):
        print("Processing Channel {}".format(c))

        print("Creating Slices...")
        chunks = split_on_silence(channel, min_silence_len=minSilence, silence_thresh=threshold )

        print("Saving slices to disk...")
        for i, chunk in enumerate(chunks):
            # Normalize the entire chunk.
            normalized_chunk = SU.match_target_amplitude(chunk, -20.0)

            fileName = "c{}s{}.wav".format(c,i)
            # Export the audio chunk with new bitrate.
            if verbose:
                print("Exporting {}...".format(fileName))
                print("\tChunk Size: {}".format(SU.ms2hms(len(chunk))))

            normalized_chunk.export(outDir + fileName, format = "wav")


if __name__ == "__main__":
    args = parser.parse_args()

    #outDir = args.outputDir if args.outputDir[-1] == "/" else  args.outputDir + "/"

    slice_clip(args.input, args.outputDir, args.minSilenceLen, args.silenceThreshold, args.verbose)

    print("Done.")
