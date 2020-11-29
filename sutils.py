from pydub import AudioSegment
from random import random


# Returns 'True' with 'prob' probability
def doChance(prob):
    assert 0.0 <= prob <= 1.0
    return random() <= prob


# converts miliseconds (int) to hours minutes seconds (str)
def ms2hms(millis):
    if millis < 1000:
        return "{}ms".format(millis)
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


# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)


#reads in config file and returns a list of active groups
def parseConfig():
    with open("createSound.cfg", 'r') as configFile:
        result = [line[1:].strip() for line in configFile if line[0] == '+']
        if not result:
            print("config error: no sound directories included.")
            exit(1)
        return result







