import yaml
import logging as log

class Configuration:

	def __init__(self, configuration_file_name):
		'''
		Initialize a configuration object by receiving its file name.
		'''
		log.debug("Reading file {file}".format(file=configuration_file_name))
		with open(configuration_file_name, 'r') as config_data_stream:
			self._config = yaml.safe_load(config_data_stream)

	def config(self):
		return self._config

