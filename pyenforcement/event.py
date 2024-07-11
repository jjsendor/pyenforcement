# standard libraries
import datetime
import dateutil.parser
import json
import re

# 3rd party libraries

# project libraries
import enforcement

class GenericEvent():
	"""
	Event format used to submit events to the OpenDNS enforcement API
	"""
	def __init__(self):
		self.device_id = None
		self.device_version = None
		self.event_time = None
		self.alert_time = None
		self.dst_domain = None
		self.dst_url = None
		self.protocol_version = '1.0a'
		self.provider_name = 'Security Platform'
		self.dst_ip = None
		self.event_severity = None
		self.event_type = None
		self.event_description = None
		self.event_hash = None
		self.file_name = None
		self.file_hash = None
		self.external_url = None
		self.disable_dst_safeguards = None
		self.src = None

	def _convert_timestamp(self, timestamp):
		"""
		Convert the timestamp is in the format:

		2013-02-08T09:30:26Z
		"""
		result = None

		if type(timestamp) == type(datetime.datetime.now()):
			result = timestamp.utcnow().isoformat() + 'Z'
		elif type(timestamp) == type(''):
			try:
				date_obj = dateutil.parser.parse(timestamp)
				result = date_obj.utcnow().isoformat() + 'Z'
			except Exception, err:
				# not a valid timestamp
				result = None

		return result

	def _validate_domain(self, possible_domain):
		"""
		Check to see if the specified string is conforms to the domain spec, RFC3986 
		"""
		# domain regex from discussion at http://stackoverflow.com/questions/10306690/domain-name-validation-with-regex
		# answer by Andre Domaszek, https://stackoverflow.com/a/41193739
		pattern = re.compile(r'^(?=.{1,253}\.?$)(?:(?!-|[^.]+_)[A-Za-z0-9-_]{1,63}(?<!-)(?:\.|$)){2,}$')
		
		m = pattern.search(possible_domain.strip())
		if m:
			return possible_domain
		else:
			return None

	def required_properties(self):
		"""
		Return a list of the required properties for events to be accepted by the API
		"""
		return [
			'device_id',
			'device_version',
			'event_time',
			'alert_time',
			'dst_domain',
			'dst_url',
			'protocol_version',
			'provider_name'
			]

	def optional_properties(self):
		"""
		Return a list of optional properties for events
		"""
		return [
			'dst_ip',
			'event_severity',
			'event_type',
			'event_description',
			'event_hash',
			'file_name',
			'file_hash',
			'external_url',
			'src',
			'disable_dst_safeguards',
			]

	def _is_valid(self, return_failed_properties=False):
		"""
		Check to see if this event is valid and conforms to the specification

		Details available at http://s-platform.opendns.com/#eventformat
		"""

		is_valid = True
		failed_properties = []
		for obj_property in self.required_properties():
			current_value = getattr(self, obj_property)
			if not current_value or current_value == '':
				failed_properties.append(obj_property)
				is_valid = False

		if return_failed_properties:
			return return_failed_properties
		else:
			return is_valid

	def get_missing_properties(self):
		"""
		Return a list of required properties do not have a value assigned
		"""
		return self._is_valid(return_failed_properties=True)

	def to_json(self):
		"""
		Convert the event to a JSON document
		"""
		properties = self.required_properties() + self.optional_properties()

		if not self._is_valid(): return None

		doc = {}
		for obj_property in properties:			
			# make sure we use the API name and not the pythonic one
			_words = obj_property.split('_')
			_words[1:] = map(str.title, _words[1:])
			api_name = ''.join(_words)

			current_value = getattr(self, obj_property)
			# make sure the value conforms to spec
			if obj_property.endswith('_time'):
				current_value = self._convert_timestamp(current_value)
			elif obj_property.endswith('_domain'):
				current_value = self._validate_domain(current_value)
			elif api_name == 'protocolVersion':
				current_value = '1.0a' # currently the only accepted value
			elif api_name == 'providerName':
				current_value = 'Security Platform' # currently the only accepted value
			elif api_name == 'disableDstSafeguards':
				if current_value != True:
					current_value = None
			
			if not current_value or current_value == '':
				continue # don't convert this property
			else:
				doc[api_name] = current_value

		json_obj = None
		try:
			json_obj = json.loads(json.dumps(doc))
		except Exception, err:
			raise(enforcement.OpenDnsApiException('Could not convert the event to a valid JSON document. Threw exception: {}'.format(err)))

		return json_obj
