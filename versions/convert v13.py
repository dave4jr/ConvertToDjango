#*========================== #
#*  Author:		Dave Luke Jr
#*  Company:	CenterStack.io
#*  Description:	Convert to Static
#*========================== #
import os, sys, codecs, re, shutil, zipfile, urllib2, urllib
import urlparse
from easydict import EasyDict
from pprint import pprint as pp
import bs4, pyautogui
sys.stdout = codecs.getwriter('utf8')(sys.stdout)


class InitVariables():
	def __init__(self):

		#	Input Settings
		# ===============================================
		self.PARSER				= "lxml"																			# Parser Options: html.parser, lxml, html5lib
		self.AUTHOR				= "CenterStack"																		# What you want the meta.author.content tag to equal
		self.TITLE					= "CenterStack"																		# What you want the meta.title.string to equal
		self.COUNTER				= 0
		self.RESTORE_WARNING		= False																			# Show warning before restoring template files?
		self.STATIC				= "{% load staticfiles %}"																# Django load statement for static files
		self.LINK_ATTRIBUTES		= ["href", "src", "data-src", "data-src-retina"]													# List of attributes to select with Beautiful Soup and then to convert to Django syntax - this list will update and get more robust as more people use this tool
		self.URLCONF_INDEX			= "/sys/centerstack/site/apps/metronic/templates/metronic/admin_1/index.html"						# This is the file that is used to pull the information needed to build the urlconf automatically - default is index.html
		
		#	Calculated Variables
		# ===============================================
		self.APP_NAME				= "metronic"																		# This is the name of the app name and folder name
		self.APP_DIR				= os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'apps', self.APP_NAME)		# High-level application directory containing all of the individual apps
		self.STATIC_DIR				= os.path.join(self.APP_DIR, 'static', 'static_dirs', self.APP_NAME)									# Static file directory - bucketed into a folder with the name of the app to keep the static files from other apps from overlapping

		#	Template Settings
		# ========================================= #
		self.THEME_DIR				= "/sys/centerstack/materials/templates/metronic/html"										# Enter the directory containing HTML files from the original theme
		self.THEME				= self.get_templates(self.THEME_DIR)
		self.THEME_FILES			= self.THEME.files
		self.THEME_FOLDERS			= self.THEME.folders

		self.TEMPLATE_DIR			= os.path.join(self.APP_DIR, "templates", self.APP_NAME)										# Folder that contains all your template HTML files
		self.TEMPLATE_FILES			= self.get_templates(self.TEMPLATE_DIR).files
		self.TEMPLATE_BACKUP		= "/sys/centerstack/site/scripts/convertToDjango/backups/%s.zip" % self.APP_NAME					# ZIP File -- Backup file of all original template HTML files


	def is_template(self, file):
		return True if file.lower().endswith('.html') else False


	def get_templates(self, dir):
		'''
		templates 				= object that contains the file, filename, folder instances
		templates.files 			= file instance
		templates.filenames 		= filename instance
		templates.folder 			= folder instance
		'''
		templates = EasyDict()
		templates_files = []
		templates_filenames = []
		templates_folders = []
		templates_basepaths = []
		templates_transfer_filename_underscores = []
		templates_transfer_filename_dashes = []

		for root, dirs, filenames in os.walk(dir):
			for filename in filenames:
				folder = os.path.basename(root)
				path = os.path.join(root, filename)
				basepath = path[(len(dir)+1):len(path)]
				transfer_filename_underscore = basepath.replace("/", "_")
				transfer_filename_dash = transfer_filename_underscore.replace("_", "-")

				if self.is_template(filename):
					templates_files.append(path)
					templates_filenames.append(filename)
					templates_folders.append(folder)
					templates_basepaths.append(basepath)
					templates_transfer_filename_underscores.append(transfer_filename_underscore)
					templates_transfer_filename_dashes.append(transfer_filename_dash)

		templates.files = templates_files
		templates.folders = templates_folders
		templates.basepaths = templates_basepaths

		templates.filename = templates_filenames
		templates.transferNameUS = templates_transfer_filename_underscores
		templates.transferName = templates_transfer_filename_dashes
		
		return templates


# ==================================================#
#	Transfer Tempalte Files
# ==================================================#
class TransferTemplateFiles(InitVariables):
	def run(self):
		templates = self.get_templates(self.THEME_DIR)
		files = templates.files
		filenames = templates.filenames
		folders = templates.folders
		transferName = templates.transferName

		for ii in range(len(files)):
			transferPath = os.path.join(self.TEMPLATE_DIR, transferName[ii])
			shutil.copy(files[ii], transferPath)
		print "Transfer Complete!"


# ==================================================#
#	Reload new copies of all the templates in the templates folder
# ==================================================#
class RestoreTemplateFiles(InitVariables):
	def run(self):
		response = pyautogui.confirm("Restore Template Files?") if self.RESTORE_WARNING else "OK"
		if  response == "OK":
			k = 1
			print "[*] Removing Current Template Files...\n------------------------------------"
			for file in self.TEMPLATE_FILES:
				os.remove(file)
				print "%s) %s" % (k, file)
				k += 1
				
			with zipfile.ZipFile(self.TEMPLATE_BACKUP, "r") as z:
				print "\n[*] Extracting Backup Template Files..."
				z.extractall(self.TEMPLATE_DIR)

			try:
				shutil.rmtree(os.path.join(self.TEMPLATE_DIR,"__MACOSX"))
				print "\n[*] Removing __MACOSX file"
			except:
				pass
		print "\n[*] Process Complete (%s of %s Template Files Restored).\n" % (k - 1, len(self.TEMPLATE_FILES))


# ==================================================#
#	Compile Source to Django Static Tags
# ==================================================#
class ConvertToDjango(InitVariables):

	def create_soup(self, template):
		self.f = open(template,'r+')
		self.soup = bs4.BeautifulSoup(self.f, self.PARSER,from_encoding="utf-8")
			
	def insert_load_static_declaration(self):
		try:
			html_tag = self.soup.find("html")
			html_tag.insert_before(self.STATIC)
		except:
			pass

	def compile_meta(self):
		try:
			self.soup.find("meta",{"name":"author"})['content'] = self.AUTHOR
			if self.TITLE == "default":
				pass
			else:
				self.soup.find("title").string = self.TITLE
		except:
			pass


	def compile_links(self):
		for attribute in self.LINK_ATTRIBUTES:
			attrs = self.soup.find_all(attrs = {attribute: True})

			# Check to see if link path starts with double dots (..) and if so, remove
			for attr in attrs:
				tag = attr[attribute]
				if tag[0:3] == "../":
					tag = tag.replace("../", "")
				try:
					f, ext = os.path.splitext(tag)
				except:
					pass

				# Check if link is a static reference or a template HTML file
				if os.path.isfile(os.path.join(self.STATIC_DIR, tag)):
					attr[attribute] = "{%% static '%s/%s' %%}" % (self.APP_NAME, tag)
				elif ext == ".html" and tag[0:4] != "http":
					urlUS = "%s_%s_%s" % (self.APP_NAME, self.THEME_FOLDERS[self.COUNTER], f)
					url = urlUS.replace("_", "-")
					attr[attribute] = "{%% url '%s' %%}" % url
				else:
					pass

	def save(self, template):
		try:
			self.f.close()
			html = self.soup.prettify("utf-8")
			with open(template, "wb") as file:
				 file.write(html)
		except:
			pass

	def run(self):
		try:
			for template_file in self.TEMPLATE_FILES:
				self.create_soup(template_file)

				# Checks to see if template has been compiled already
				if re.search(self.STATIC, self.soup.prettify()):
					print "%s --- Already Processed! Skipping..." % os.path.basename(template_file)
					continue
				else:
					self.insert_load_static_declaration()
					self.compile_meta()
					self.compile_links()
					self.save(template_file)
					print os.path.basename(template_file)
				self.COUNTER += 1
			print "\nProcess Complete!\n"
		except Exception, e:
			print e


# ==================================================#
#	Generate URL Conf
# ==================================================#
class CreateURLCONF(InitVariables):
	def run(self):
		urlconfs = []
		for theme in self.THEME_FILES:
			folder_file = theme[(len(self.THEME_DIR)+1):len(theme)]

			# Creating the 3 sections of the URLConf
			conf_url, ext = os.path.splitext(folder_file)
			conf_template = folder_file.replace("/","_").replace("_", "-")
			conf_name = "%s-%s" % (self.APP_NAME, conf_url.replace("/","_").replace("_", "-"))

			urlconf = "url(r'^%s/$', '%s.views.navigation', {\"template\":\"%s\"}, name=\"%s\")," % (conf_url, self.APP_NAME, conf_template, conf_name)
			urlconfs.append(urlconf)

		k = 1
		for ii in range(len(urlconfs)):
			if k == 1:
				print "urlpatterns += patterns('',"
				print "	%s" % urlconfs[ii]
				k += 1
			if k < 250:
				print "	%s" % urlconfs[ii]
				k += 1
			if k == 250:
				print "	%s\n)\n\n" % urlconfs[ii]
				k = 1


		


# ==================================================#
#	Run
# ==================================================#
def run(action):
	actions = ["convert","con","urlconf","url","transfer","tr","restore","re","init"]
	if action not in actions and not action.isspace():
		print "Action must be choosen from one of the following keywords: convert, urlconf, transfer, or restore"
	elif action in ["convert", "con"]:
		ConvertToDjango().run()
	elif action in ["urlconf", "url"]:
		CreateURLCONF().run()
	elif action in ["transfer", "tr"]:
		TransferTemplateFiles().run()
	elif action in ["restore", "re"]:
		RestoreTemplateFiles().run()
	elif action == "init":
		InitVariables()
	else:
		print "Please enter an action into the run function!"
	

run("convert")




