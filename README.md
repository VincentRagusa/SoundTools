# Dependencies
ffmpeg

pydub

#  First Time setup
create a directory for your sound library

"mkdir library"

# Adding new sounds to the library
create a directory in the sound library for the new sounds

"mkdir library/newSound"

slice an input file and store the sounds in the new library folder

"python3 slice.py myInput.mp3 library/newSound"

(re)build the sound cache

"python3 buildCache.py library"

This step also generates groups.cfg which is used to generate sounds.

# Generating an output file

Choose the library groups you wish to include in the output file by modifying groups.cfg to indicate each group to include with a "+" followed by a space " " followed by the group name. For convenience, you may simply replace the "+" with another symbol such as "-" to remove the sound group from the config.

Run the generator program and specify an output name

"python3 generate.py output.mp3"
