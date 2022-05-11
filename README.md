##################################################################
#
#					Using Python Script
#
##################################################################

python
	Command always starts with python, use however you access python from command line

extract_audio_features.py
	next comes the name of the python file

Methods | select a method of how to extract features

	get_all_features: this method extracts, global, sliding window and lld features

	get_lld_features: this method extracts only lld features

	get_global_features: this method extract only global features

	get_sliding_window_function_features: this method extracts global features by sliding window

Flags | PATH and OUTPATH must be specified, all other flags have a default. 

	--PATH : path to wav file or directory of wav files. path to directory only works with get_all_features method

	--OUTPATH: outpath where feature files will be created

	--window_size: length in seconds of the window that the features will be extracted. Must be greater than 0. Default is 1 second.

	--overlap: length in seconds of the overlap time in the window. When window_size equals overlap, the time windows are consecutive. Example: if the window_size and overlap are set to 2 seconds then features will be extracted from 0:00->0:02, 0:02->0:04, etc. overlap must be less than the window_size and greater than 0. Default is 1 second

	--opensmile_config: configuration of audio features that will be extracted. Default is set to eGeMAPSv02. Other files included with py-opensmile can be found here. 



##################################################################
#
#					Usage Examples
#
##################################################################

#when extracting from a single wav file, all methods work. 
python extract_audio_features.py get_sliding_window_function_features --PATH /data/audio/my_audio.wav --OUTPATH extracted_features/audio/

#when extracting from a directory containing wav files, get_all_features method works.
python extract_audio_features.py get_all_features --PATH /data/audio/ --OUTPATH extracted_features/audio/

#specifying other things, when window_size and overlap are equal, then the audio segments are consecutive with no overlap.
python extract_audio_features.py get_all_features --PATH /data/audio/ --OUTPATH extracted_features/audio/ --windowsize 10 --overlap 10 --opensmile_config 

##################################################################
#
#					DOCKER
#
##################################################################

https://hub.docker.com/repository/docker/hali02/pyopensmile-sliding-window

#build docker
docker build -f ExtractPyopensmileFeatures.Dockerfile -t extract_opensmile .

#run docker
docker run -it -v /Users/desktop/extract_pyopensmile_feaatures:/code extract_opensmile
