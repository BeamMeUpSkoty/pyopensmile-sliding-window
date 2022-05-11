'''
Created on Apr 20, 2022

@author: hali02
'''
#reference for egemaps features from opensmile https://mediatum.ub.tum.de/doc/1082431/1082431.pdf

import os 
import shutil
import fire
import re

from pydub import AudioSegment
from pyannote.core import SlidingWindow

import opensmile

import pandas as pd


class OpensmileFeaturesFromSlidingWindow(object):
	"""
	"""
	def __init__(self, PATH, OUTPATH='', window_size=1, overlap=1, opensmile_config='eGeMAPSv02'):
		self.path = PATH
		self.file_name = os.path.basename(self.path)[:-4]
		self.OUTPATH = OUTPATH + '/'
		self.window_size = window_size
		self.overlap = overlap
		self.opensmile_config = opensmile_config
		
		if os.path.isfile(self.path):
			self.audio = AudioSegment.from_wav(self.path)
	
	#####################################################################
	#
	#  Utility
	#
	#####################################################################

	@staticmethod
	def _remove_tmp_file(tmp_path='tmp/', verbose=False):
		"""
		Parameters
		----------
		tmp_path : string, optional
			default set to tmp/
		verbose : boolean, optional
			prints statement when true

		Returns
		----------
		remove tmp file once finished calculating features.
		"""
		if os.path.isdir(tmp_path):
			if verbose:
				print('### Removing tmp file: ', tmp_path, ' ###')
			shutil.rmtree(tmp_path, ignore_errors=True)
		return
	
	
	@staticmethod
	def _create_tmp_file(tmp_path='tmp/', verbose=False):
		"""
		Parameters
		----------
		tmp_path : string, optional
			default set to tmp/
		verbose : boolean, optional
			prints statement when true
			
		Returns
		----------
		create tmp file once finished to store audio segments.
		"""
		if os.path.isdir(tmp_path) == False:
			if verbose:
				print('### creating tmp file: ', tmp_path, ' ###')
			os.mkdir(tmp_path)		
		return


	def _get_duration(self):
		""" get duration of audio file in seconds.

		Returns
		----------
		duration of audio in seconds
		"""
		return self.audio.duration_seconds

	#####################################################################
	#
	#  Sliding Window
	#
	#####################################################################
		
	def _make_sliding_windows(self, duration=1, overlap=1):
		"""generate audio segments with sliding window over the audio file. When duration
		equals overlap, there is no overlap in audio segments. 

		Parameters
		----------
		duration : int, optional
			window size in seconds, by default 1 sec
		overlap : float, optional
			overlap between consecutive chunks in seconds, by default 1 sec

		Returns
		-------
		sliding_window : pyannote.core.SlidingWindow
			list of audio segments of pyannote.core.Segments 
			Example:    [ 00:00:00.000 -->  00:00:03.000]
						[ 00:00:00.500 -->  00:00:03.500]
						....
		"""        
		audio_length = self._get_duration()
		return SlidingWindow(duration, overlap, 0, audio_length-duration+overlap)


	def split_audio_by_window_size(self, tmp_path='tmp/', window_size=10000):
		"""
		split wav file into multiple wave files. 
		new wave files have length of window_size
		split files are saved in tmp/ with naming convention startTime_endTime.wav
		
		Parameters
		----------
		window_size: int
			window size in milliseconds. Default is 10000ms or 1 second
			
		Returns
		----------
		tmp/ : directory
			returns a directory tmp/ of audio files of size window_size
			Feautres can then be computed from each of the split files. 
		"""
		window_paths = []

		#create a new tmp file to store newly spliced audio file
		OpensmileFeaturesFromSlidingWindow._remove_tmp_file(tmp_path)
		OpensmileFeaturesFromSlidingWindow._create_tmp_file(tmp_path)

		#cut audio file into window-sized chunks
		windows = self._make_sliding_windows(self.window_size, self.overlap) 
		
		#store chunks in tmp file with the naming convention startTime_endTime.wav (this is necessary to get the time alignment later
		for window in windows:
			segment = self.audio[window.start*1000:window.end*1000]
			window_path = tmp_path + str(window.start) + '_' + str(window.end) + '.wav'
			segment.export(window_path, format='wav')
			window_paths.append(window_path)
		return window_paths

	#####################################################################
	#
	#  Feature Methods
	#
	#####################################################################

	def extract_opensmile_functional_features(self, segment):
		"""
		Parameters
		----------
		segment : string
			path to audio segment

		Returns
		----------
		pandas dataframe of opensmile functional features.
		"""
		smile_functionals = opensmile.Smile(feature_set=opensmile.FeatureSet.eGeMAPSv02, feature_level=opensmile.FeatureLevel.Functionals,)
		#smile_lld = opensmile.Smile(feature_set=opensmile.FeatureSet.eGeMAPSv02, feature_level=opensmile.FeatureLevel.LowLevelDescriptors,)
		return smile_functionals.process_file(segment)

	def extract_opensmile_lld_features(self, segment):
		"""
		Parameters
		----------
		segment : string
			path to audio segment

		Returns
		----------
		pandas dataframe of opensmile low level dedscription features.		
		"""
		smile_lld = opensmile.Smile(feature_set=opensmile.FeatureSet.eGeMAPSv02, feature_level=opensmile.FeatureLevel.LowLevelDescriptors,)
		return smile_lld.process_file(segment)


	#####################################################################
	#
	#  Feature Output Methods
	#
	#####################################################################

	def get_sliding_window_function_features(self, tmp_path='tmp/', verbose=True):
		"""		
		Returns
		----------
		pandas dataframe of opensmile features.	
		"""

		all_window_functional_features = []
		#all_winddow_lld_features= []

		audio_segments = self.split_audio_by_window_size()

		for segment_path in audio_segments:
			functional_features = self.extract_opensmile_functional_features(segment_path)
			#add start and end times to csv
			functional_features['start_time'] = re.findall('(?<=\/)(.*?)(?=\_)', segment_path)[0]
			functional_features['end_time'] = re.findall('(?<=\_)(.*?)(?=\.)', segment_path)[0]

			all_window_functional_features.append(functional_features)
		
		all_functional_features = pd.concat(all_window_functional_features)
		
		all_functional_features.to_csv(self.OUTPATH + self.file_name + '_sliding_window_functionals.csv')
		
		if verbose:
			print('### created ', str(self.file_name) + '_sliding_window_functionals.csv', '###')
		
		#remove final /tmp file
		OpensmileFeaturesFromSlidingWindow._remove_tmp_file(tmp_path)

		return

	def get_global_features(self, tmp_path='tmp/', verbose=True):
		""" compute features without sliding window
		Returns
		----------
		pandas dataframe of opensmile low level dedscription features.	
		"""

		functional_features = self.extract_opensmile_functional_features(self.path)
		functional_features.to_csv(self.OUTPATH + self.file_name + '_functionals.csv')

		if verbose:
			print('### created ', self.file_name + '_functionals.csv', '###')

		#remove final /tmp file
		OpensmileFeaturesFromSlidingWindow._remove_tmp_file(tmp_path)
		
		return

	def get_lld_features(self, tmp_path='tmp/', verbose=True):
		"""	computes low level descriptor features	
		Returns
		----------
		pandas dataframe of opensmile low level dedscription features.	
		"""

		lld_features = self.extract_opensmile_lld_features(self.path)
		lld_features.to_csv(self.OUTPATH + self.file_name + '_llds.csv')

		if verbose:
			print('### created ', str(self.file_name) + '_llds.csv', '###')
		
		#remove final /tmp file
		OpensmileFeaturesFromSlidingWindow._remove_tmp_file(tmp_path)

		return

	def get_all_features(self):
		""" Returns three csv files for each wav file (one for each feature set) to specified output path.
		If a directory is passed through for self.PATH, all files will be iterated through.
		If a file is passed through for self.PATH, that file will be evaluated.

		Returns
		----------
		*filename*_functionals.csv : csv
			csv file of global functional features
		*filename*_llds.csv : csv
			csv file of low level descriptors features
		*filename*_sliding_window_functionals.csv : csv 
			csv file of sliding window functional features
		"""
		#check to see if path is a directory
		if os.path.isdir(self.path):
			#get all files in directory
			for filename in os.listdir(self.path):
				#files to skip
				if filename not in ['.DS_Store']:
					#create new class object with file in directory, passing through parameters
					new_object = OpensmileFeaturesFromSlidingWindow(PATH=self.path+'/'+filename, OUTPATH=self.OUTPATH, window_size=self.window_size, overlap=self.overlap, opensmile_config=self.opensmile_config)

					#extract all feature methods using new object
					new_object.get_sliding_window_function_features()
					new_object.get_global_features()
					new_object.get_lld_features()
		#if path is a file, this is checked when self.PATH is set in the init for the class
		else:
				self.get_sliding_window_function_features()
				self.get_global_features()
				self.get_lld_features()
		return


if __name__ == '__main__':
	"""
	creates command line interface
	"""
	fire.Fire(OpensmileFeaturesFromSlidingWindow)
