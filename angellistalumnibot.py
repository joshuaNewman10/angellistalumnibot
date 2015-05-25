import requests
import oauth2 as oauth
import urlparse
import ipdb as ipdb
import re
import angellist
reload(angellist)
import urllib2
from progressbar import *
from pandas import DataFrame

#######################################################################################
# Scrapes AngelList for alumni.							                              #
#                                                                                     #
# Author: Troy Shu                                                                    #
# Email : tmshu1@gmail.com                                                            #
# Web: http://www.troyshu.com                                                         #
#                                                                                     #
#######################################################################################


class AngellistAlumniBot:
	def __init__(self):
		self.al = angellist.AngelList()
		#this is my access token. if you have your own access token, please use it
		self.al.access_token = '436c4e00aa39c52f0c04e68a5373d407'

		self.locationTagIdMap = {
			'NYC':1664,
			'SV':1681,

		} #maps a city string to angellist id for that location


	def _findStartups(self, city, topPct, followMin):
		print 'getting all startups in %s:' % city

		getLocationId = self.locationTagIdMap[city]

		#get all startups in city
		startupUrls = []
		startupNames = []
		pageCount = 1
		count = 0
		perPage = 50
		stop = False
		#while not stop
		while count < 1:
			print 'getting page %s of startups...' % (pageCount)

			#get most popular startups first
			search_response = self.al.getTagsStartups(self.al.access_token, getLocationId, order='popularity', per_page = perPage, page=pageCount)

			#extract all startup urls
			startups = search_response['startups']

			for startup in startups:
				#if start up is hidden, continue
				if startup['hidden']:
					continue

				startupUrls.append(startup['angellist_url'])
				startupNames.append(startup['name'])
				

				#if we've reached a min follower count, break
				if followMin and int(startup['follower_count'])<followMin:
					print 'reached min follower count of %s' % followMin
					stop = True
					break


			count += perPage
			#if we reached the end
			if count >= int(search_response['total']):
				print 'reached the end of AngelList startups for %s' % city
				stop = True
			#if we reached more than topPct of most popular startups (by followers)
			if count > topPct*float(search_response['total']):
				print 'finished grabbing top %s of startups by follower count' % topPct
				stop = True


			pageCount += 1
		
		
		return startupUrls, startupNames
	
	def _parseOutEmployeeURLS(self, data):
		# '<a href="https://angel.co/briansin" class="profile-link" data-id="737" data-type="User">Brian Singerman</a>'
		urlMatch = re.search(r'https://angel.co/[\w\d]*', data)
		if hasattr(urlMatch, 'group'):
			return urlMatch.group()
		else:
			return None;

	def _scrapeEmployeePage(self, employeeURL):
		print('temp')
		

	def _scrapeStartupPageForEmployees(self, startupURL):
		employeeList = []
		employeeURLS = []
		try:
			response = urllib2.urlopen(startupURL)
			page_source = response.read()
		except:
			#in case startup page on angellist doesnt exist for some reason
		  return None
		lines = page_source.split('\n')
		employeesSection = ''

		for lineCount in range(0, len(lines)):
			line = lines[lineCount]
			if 'profile-link' in line:
				employeeList.append(lines[lineCount])

		for employeeData in employeeList:
			employeeURLS.append(self._parseOutEmployeeURLS(employeeData))
    
    #filter out bad names
		return filter(None, employeeURLS) 


	def _scrapeStartupPageForFounder(self, startupUrl):
		try:
			response = urllib2.urlopen(startupUrl)
			page_source = response.read()
			print('page source',page_source)
		except:
			#for some reaosn, if the startup's page on angellist doesn't exist or something
			return None
		lines = page_source.split('\n')
		print('lines!', lines)
		founderLine = ''
		#hacky: use regex to scrape founder's name
		for lineCount in range(0,len(lines)):
			line = lines[lineCount]
			if '<meta content=\'FOUNDER\'' in line:
				founderLine = lines[lineCount+1]
				break
		if founderLine:
			founderName = re.findall(r'<meta content=\'(.*)\' name=',founderLine)[0]
			return founderName
		else:
			return None

	def _getFounderPageFromName(self, founderName):
		#search angellist for foundername
		results = self.al.getSearch(self.al.access_token, query = founderName)
		
		#get first result's page
		try:
			return results[0][0]['url']
		except:
			return None


	def _getEmployees(self, startupUrls, startupNames):
		startupUrlAndNames = zip(startupUrls, startupNames)
		allEmployees = [] #Array list of all employees
		employeesAndStartups = {} #Object of startup and their employee list

		print 'scraping founder names from AngelList startup pages...'
		pbar = ProgressBar(maxval=len(startupUrls))
		pbar.start()
		#get startup page
		count = 0
		for startupUrl, startupName in startupUrlAndNames:
			#scrape employee names from startupPage
			employeeNames = self._scrapeStartupPageForEmployees(startupUrl)

			#append to master list of employees
			allEmployees.append(employeeNames)

				employeesAndStartups[startupName] = employeeNames
			  count+=1
			pbar.update(count)
		
		pbar.finish()


		# for each employee name, search, grab id
		print 'getting AngelList page for each employee...'
		pbar = ProgressBar(maxval=len(employeesAndStartups.keys()))
		pbar.start()
		count = 0
		employeesAndPages = {}
		for employeeList in employeesAndStartups.keys():
			for employeeURL in employeeList:

			employeePage = self._getEmployeePageFromName(employeeURL)
			count+=1
		# 	pbar.update(count)

		# 	if not founderPage == None:
		# 		foundersAndPages[founderName] = founderPage

		# 	else:
		# 		continue

		# pbar.finish()
		return allEmployees, 

		# return foundersAndPages, foundersAndStartups 


	def _scrapePageForCollegeTag(self, founderPage):
		try:
			response = urllib2.urlopen(founderPage)
			page_source = response.read()
		except:
			#for some reason, if the person's angellist page doesn't exist or something
			return None
		lines = page_source.split('\n')
		for line in lines:
			if 'college-tag' in line:
				try:
					college = re.findall(r'college\-tag\"><a href=.*>(.*)</a>',line)[0]
					if college:
						return college
					else:
						return None
				except:
					return None
	
	def _isHRAlumni(self, inputText):
		inputText = inputText.lower()
		if 'Hack Reactor' in inputText or 'Hack' in inputText or 'Reactor' in inputText
			return True
		else:
			return False

	def _isAlumni(self, inputText, school):
		#checks if given input text tells us if is alumni of school
		if school=='Hack Reactor':
			return self._isHRAlumni(inputText)
		else:
			raise Exception('alumni checking method for school %s not implemented yet' % school)


	def _checkCollegeTag(self, school, employeePage):
		#scrape founder page for college tag, compare
		education = self._scrapePageForCollegeTag(employeePage)
		#if we found a college tag
		if college:
			isAlumni = self._isAlumni(education, school)
			return isAlumni
		else:
			return None
	
	def _getLinkedInUrl(self, employeePage):
		#get linked in page from angellist founder page
		try:
			response = urllib2.urlopen(employeePage)
			page_source = response.read()
		except:
			#for some reason, if the person's angellist page doesn't exist
			return None
		lines = page_source.split('\n')
		linkedinUrl = ''
		for line in lines:
			if 'linked_in-link' in line:
				try:
					linkedinUrl = re.findall(r'<a href=\"(.*)\" class=\"linked_in\-link\"',line)[0]
					
					if linkedinUrl:
						return linkedinUrl
					else:
						return None
				except:
					return None
		
		return None

	def _checkLinkedinAlmaMater(self, school, employeePage):
		#first, get linked in from founder page, if there is one
		linkedInUrl = self._getLinkedInUrl(employeePage)

		if linkedInUrl==None:
			return False
		else:
			#then founder has a linked in page
			#scrape for education, see if desired school is part of it
			try:
				response = urllib2.urlopen(linkedInUrl)
				page_source = response.read()
			except:
				#probably an invalid url
				return False


			lines = page_source.split('\n')

			schools = ''
			start = None
			end = None
			lineCount = 0
			for line in lines:
				if 'overview-summary-education-title' in line:
					start = lineCount
					
				if start:
					if '</dd>' in line:
						end = lineCount
						break

				lineCount += 1
			if not start==None and not end==None:
				educationBlock = ' '.join(lines[start:end])
				educations = re.findall(r'<a href=\".*?>(.*?)</a>',educationBlock)
					
				#check if alumni, for each education person has on linked in
				for education in educations:
					if self._isAlumni(education,school):
						return True
				return False

			else:
				#education section didn't exist on linkedin page
				return False

	def _getIsAlumniFromPage(self, school, employeesAndPages):
		print 'checking if each founder graduated from %s...' % (school)
		pbar = ProgressBar(maxval=len(employeesAndPages))
		pbar.start()
		count = 0

		founderIsAlumni = {}
		for founder in employeesAndPages:
			founderPage = employeesAndPages[founder]
			#check if college tag matches
			isAlmaMaterAngellist = self._checkCollegeTag(school, founderPage)
			
			if isAlmaMaterAngellist==None:
				#check linkedin
				isAlmaMaterLinkedin = self._checkLinkedinAlmaMater(school, founderPage)

				founderIsAlumni[founder] = isAlmaMaterLinkedin
			else:
				founderIsAlumni[founder] = isAlmaMaterAngellist

			count+=1
			pbar.update(count)

		pbar.finish()
		
		return founderIsAlumni

	def findAlumniEmployees(self, city='SV', school='Hack Reactor', topPct = 0.10, followMin = None):
		#get all startups in city
		startupUrls, startupNames = self._findStartups(city, topPct, followMin)

		#get overall employee list and list for each startup of each startup
		allEmployees, startupEmployees = self._getEmployees(startupUrls, startupNames)

		#for each founder, find out if belong to input school: first angellist tag, then linkedin
		isAlumni = self._getIsAlumniFromPage(school, foundersAndPages)

		# resultDict = {}
		# for founder in isAlumni:
		# 	newrow = {}
		# 	newrow['startup'] = foundersAndStartups[founder]
		# 	newrow['isAlumni'] = isAlumni[founder]
		# 	resultDict[founder] = newrow

		# resultDf = DataFrame(resultDict).T

		# return resultDf
		return test

		
	
