# standard libraries
import dateutil.parser
import json
import re
import urlparse

# 3rd party libraries
import requests

# project libraries

class OpenDnsApiException(Exception): pass

class Api():
	"""
	Provide a simple interface to the OpenDNS Enforcement APIException

	Initial with your customer key and use the following 3 methods to work with the API:

	- Enforcement().list_domains()
	- Enforcement().add_events(events)
	- Enforcement().delete_domain(domain_name_or_id)
	"""
	def __init__(self, key, version=1.1):
		self.key = key
		self.version = version
		self.event_time_format = '%Y-%m-%dT%H:%M:%S.%z'
		self.base_url = 'https://s-platform.api.opendns.com/1.0'

	def _get(self, url_relative_path, **kwargs):
		"""
		Make an HTTP GET request to the specified URL
		"""
		params = {
			'customerKey': self.key,
			}

		if kwargs is not None:
			# merge the passed parameters with the default
			for k, v in kwargs.items():	params[k] = v

		results = None
		resp = None
		try:
			resp = requests.get('{}/{}'.format(self.base_url, url_relative_path), params=params)
			if resp.ok:
				try:
					results = resp.json()
				except Exception, err:
					raise(OpenDnsApiException('Could not convert the response from URL [{}] to JSON. Threw exception: {}'.format(resp.url, err)))
			else:
				raise(OpenDnsApiException('Unsuccessful request to URL [{}]. HTTP status {}'.format(resp.url, resp.status_code)))
		except Exception, err:
			raise(OpenDnsApiException('Unsuccessful request to URL [{}]. Threw exception: {}'.format(resp.url, err)))

		return results

	def _post(self, url_relative_path, data, **kwargs):
		"""
		Make an HTTP POST request to the specified URL
		"""
		auth_params = {
			'customerKey': self.key,
			}

		if kwargs is not None and type(data) == type({}):
			# merge the passed parameters with the default
			for k, v in kwargs.items():	data[k] = v

		results = None
		resp = None
		url = '{}/{}'.format(self.base_url, url_relative_path)
		headers = {'Content-Type': 'application/json'}
		try:
			resp = requests.post(url, headers=headers, params=auth_params, data=json.dumps(data))
			try:
				results = resp.json()
			except Exception, err:
				raise(OpenDnsApiException('Could not convert the response from URL [{}] to JSON. Threw exception: {}'.format(resp.url, err)))
			if resp.ok == False:
				raise(OpenDnsApiException('Unsuccessful request to URL [{}]. Server message: {}'.format(resp.url, results)))
		except Exception, err:
			raise(OpenDnsApiException('Unsuccessful request to URL [{}]. Threw exception: {}'.format(resp.url, err)))

		return results

	def _delete(self, url_relative_path, params={}):
		"""
		Make an HTTP DELETE request to the specified URL
		"""

		params['customerKey'] = self.key
		url = '{}/{}'.format(self.base_url, url_relative_path)
		headers = {'Content-Type': 'application/json'}
		resp = None
		try:
			resp = requests.delete(url, headers=headers, params=params)
			if resp.status_code == 204:
				return True
			elif resp.status_code == 404:
				return False
			raise(OpenDnsApiException('Server Error {}'.format(resp.json())))
		except Exception, err:
			raise(OpenDnsApiException('Could not delete the specified domain(s). Threw exception: {}'.format(err)))

	def add_events(self, events): 
		"""
		POST /events to add a domain

		events:
			One or more events in the generic event format for the API. Enabled via api.Event()
		"""
		if type(events) != type([]): events = [events]

		data = []
		for event in events: data.append(event.to_json())

		response = self._post('events', data)
		if response and response.has_key('id'):
			return response['id']
		else:
			return None

	def list_domains(self, page=1, get_all=False): 
		"""
		GET /domains to gather a list of domains already added
		"""
		# /domains returns calls in pages of 200 domains
		# each domain is returned in a dict of:
		# 	{u'id': 3238369, u'name': u'groogle.com'}
		results = {}

		# do we need to get all of the pages?
		if get_all:
			more_pages = True
			while more_pages:
				response = self._get('domains', page=page)
				for entry in response['data']:
					results[entry['name']] = entry['id']

				# are there more pages to request?
				if response and response['meta']['next']:
					# the next value is the complete URL of the next page, pull out just the page number
					next_url = urlparse.urlparse(response['meta']['next'])
					page = urlparse.parse_qs(next_url.query)['page'][0]
					#print "next page: {}".format(page)
				else:
					more_pages = False

		else:
			# get a specific page 
			response = self._get('domains', page=page)
			for entry in response['data']:
					results[entry['name']] = entry['id']

		return results

	def delete_domain(self, domain):
		"""
		DELETE /domains to delete a domain from the list
		"""
		response = None
		# did the user pass an ID or a domain?
		m = re.search('^\d+$', domain)
		if m:
			# this is an ID
			response = self._delete('domains/{}'.format(domain))
		else:
			# this is a domain name
			response = self._delete('domains', { 'where[name]': domain })

		return response
