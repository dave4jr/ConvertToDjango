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



# ==================================================#
#	Variables Class
# ==================================================#
class InitVariables():
	def __init__(self):																						# Notes:
		self.CLASSES				= ["TransferTemplateFiles", "RestoreTemplateFiles", "", "ConvertToDjango", ""]
		self.PARSER				= "lxml"																	# Parser Options: html.parser, lxml, html5lib
		self.AUTHOR				= "CenterStack"																# What you want the meta.author.content tag to equal
		self.TITLE					= "CenterStack"																# What you want the meta.title.string to equal
		self.STATIC				= "{% load staticfiles %}"														# Django load statement for static files
		self.PRODUCTION			= False																	# Production or Development?
		self.APPNAME				= "metronic"																	# This is the name of the app name and folder name
		self.URL_PREFIX				= "metronic_admin_"
		self.APPDIR				= os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'apps', self.APPNAME)
		self.STATIC_DIR				= os.path.join(self.APPDIR, 'static', 'static_dirs', self.APPNAME)
		self.TEMPLATE_FOLDER		= os.path.join(self.APPDIR, "templates", self.APPNAME)										# Folder that contains all your template HTML files
		self.TEMPLATES		 		= self.get_templates(self.TEMPLATE_FOLDER)											# List of template HTML files in the TEMPLATES_FOLDER
		self.TEMPLATE_FILES 			= self.TEMPLATES.files													# List of template HTML files in the TEMPLATES_FOLDER
		self.TEMPLATE_BACKUP_ZIP	= "/sys/centerstack/site/scripts/convertToDjango/backups/%s.zip" % self.APPNAME					# Backup .zip file of all original template HTML files
		self.TEMPLATE_TRANSFER		= "/sys/centerstack/materials/templates/metronic/html"
		self.URLCONF_INDEX			= "/sys/centerstack/site/apps/metronic/templates/metronic/admin_1/index.html"									# This is the file that is used to pull the information needed to build the urlconf automatically - default is index.html


	def is_template(self, file):
		try:
			return True if file.lower().endswith('.html') else False
		except:
			return False


	def get_templates(self, dir):
		'''
		templates 				= object that contains the file, filename, folder instances
		templates.files 			= file instance
		templates.filenames 		= filename instance
		templates.folder 		= folder instance
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
		templates.filenames = templates_filenames
		templates.folders = templates_folders
		templates.basepaths = templates_basepaths
		templates.transferNameUnderscores = templates_transfer_filename_underscores
		templates.transferName = templates_transfer_filename_dashes
		
		return templates


# ==================================================#
#	Transfer Tempalte Files
# ==================================================#
class TransferTemplateFiles(InitVariables):
	def transfer_files(self):
		templates = self.get_templates(self.TEMPLATE_TRANSFER)
		files = templates.files
		filenames = templates.filenames
		folders = templates.folders
		transferName = templates.transferName

		for ii in range(len(files)):
			transferPath = os.path.join(self.TEMPLATE_FOLDER, transferName[ii])
			shutil.copy(files[ii], transferPath)


# ==================================================#
#	Reload new copies of all the templates in the templates folder
# ==================================================#
class RestoreTemplateFiles(InitVariables):

	def restore_files(self):
		response = pyautogui.confirm("Restore Template Files?") if self.PRODUCTION else "OK"
		if  response == "OK":
			k = 1
			print "[*] Removing Current Template Files...\n------------------------------------"
			for file in self.TEMPLATE_FILES:
				os.remove(file)
				print "%s) %s" % (k, file)
				k += 1
				
			with zipfile.ZipFile(self.TEMPLATE_BACKUP_ZIP, "r") as z:
				print "\n[*] Extracting Backup Template Files..."
				z.extractall(self.TEMPLATE_FOLDER)

			try:
				shutil.rmtree(os.path.join(self.TEMPLATE_FOLDER,"__MACOSX"))
				print "\n[*] Removing __MACOSX file"
			except:
				pass
		print "\n[*] Process Complete (%s of %s Template Files Restored).\n" % (k, len(self.TEMPLATE_FILES))

	def restore_folder(self, template_folder_to_delete):
		response = pyautogui.confirm("Restore Template Files?") if self.PRODUCTION else "OK"
		if  response == "OK":
			try:
				shutil.rmtree(template_folder_to_delete)
			except:
				pass
			
			with zipfile.ZipFile(self.TEMPLATE_BACKUP_ZIP, "r") as z:
				z.extractall(os.path.join(template_folder_to_delete,".."))
			try:
				shutil.rmtree(os.path.join(template_folder_to_delete,"..","__MACOSX"))
			except:
				pass
		print "Template folder has been restored."


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

		#	HREF
		# ========================================= #
		hrefs = self.soup.find_all(attrs = {'href': True})
		for tag in hrefs:
			href = tag['href']
			if href[0:3] == "../":
				href = href.replace("../", "")
			try:
				f, ext = os.path.splitext(href)
			except:
				pass

			if os.path.isfile(os.path.join(self.STATIC_DIR, href)):
				tag['href'] = "{%% static '%s/%s' %%}" % (self.APPNAME, href)
			elif ext == ".html":
				if self.URL_PREFIX == 0 or self.URL_PREFIX == "":
					tag['href'] = "{%% url '%s' %%}" % f
				else:
					tag['href'] = "{%% url '%s%s' %%}" % (self.URL_PREFIX, f)
			else:
				pass

		#	SRC
		# ========================================= #
		srcs = self.soup.find_all(attrs = {'src': True})
		for tag in srcs:
			src = tag['src']
			if src[0:3] == "../":
				src = src.replace("../", "")
			try:
				f, ext = os.path.splitext(src)
			except:
				pass

			if os.path.isfile(os.path.join(self.STATIC_DIR, src)):
				tag['src'] = "{%% static '%s/%s' %%}" % (self.APPNAME, src)
			elif ext == ".html":
				if self.URL_PREFIX == 0 or self.URL_PREFIX == "":
					tag['src'] = "{%% url '%s' %%}" % f
				else:
					tag['src'] = "{%% url '%s%s' %%}" % (self.URL_PREFIX, f)
			else:
				pass


		#	DATA-SRC
		# ========================================= #
		data_srcs = self.soup.find_all(attrs = {'data-src': True})
		for tag in data_srcs:
			data_src = tag['data-src']
			if data_src[0:3] == "../":
				data_src = data_src.replace("../", "")
			try:
				f, ext = os.path.splitext(data_src)
			except:
				pass

			if os.path.isfile(os.path.join(self.STATIC_DIR, data_src)):
				tag['data-src'] = "{%% static '%s/%s' %%}" % (self.APPNAME, data_src)
			elif ext == ".html":
				if self.URL_PREFIX == 0 or self.URL_PREFIX == "":
					tag['data-src'] = "{%% url '%s' %%}" % f
				else:
					tag['data-src'] = "{%% url '%s%s' %%}" % (self.URL_PREFIX, f)
			else:
				pass


		#	DATA-SRC-RETINA
		# ========================================= #
		data_src_retinas = self.soup.find_all(attrs = {'data-src-retina': True})
		for tag in data_src_retinas:
			data_src_retina = tag['data-src-retina']
			if data_src_retina[0:3] == "../":
				data_src_retina = data_src_retina.replace("../", "")
			try:
				f, ext = os.path.splitext(data_src_retina)
			except:
				pass

			if os.path.isfile(os.path.join(self.STATIC_DIR, data_src_retina)):
				tag['data-src-retina'] = "{%% static '%s/%s' %%}" % (self.APPNAME, data_src_retina)
			elif ext == ".html":
				if self.URL_PREFIX == 0 or self.URL_PREFIX == "":
					tag['data-src-retina'] = "{%% url '%s' %%}" % f
				else:
					tag['data-src-retina'] = "{%% url '%s%s' %%}" % (self.URL_PREFIX, f)
			else:
				pass


	def compile_canvas_logo(self):
		try:
			ddls = self.soup.find_all(attrs={'data-dark-logo' : True})
			for ddl in ddls:
				logo = ddl['data-dark-logo']
				if logo[0:7] != "http://":
					logo_new = "images/logo-transparent.png"
					ddl['data-dark-logo'] = "{%% static '%s/%s' %%}" % (self.APPNAME, logo_new)
		except:
			pass


	#	Save
	# ========================================= #
	def save(self, template):
		try:
			self.f.close()
			html = self.soup.prettify("utf-8")
			with open(template, "wb") as file:
				 file.write(html)
		except:
			pass


	#	Main Loop through all templates
	# ========================================= #
	def convert(self):
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
					self.compile_canvas_logo()
					self.save(template_file)
					print os.path.basename(template_file)
			print "\nProcess Complete!\n"
		except Exception, e:
			print e


# ==================================================#
#	Generate URL Conf
# ==================================================#
class CreateURLCONF(ConvertToDjango):
	# def create_from_templates(self):

	def create_from_links(self):
		self.create_soup(self.URLCONF_INDEX)
		nav_as = self.soup.find("nav").find_all("a")
		for nav_a in nav_as:
			try:
				nav_a_href = nav_a['href']
				if nav_a_href[0:7] != "http://":
					if nav_a_href[0] != "#":
						urlconf_name = nav_a_href[0:nav_a_href.find(".html")]
						url_1_2 = str(urlconf_name) + ".html"
						url_1_3 = urlconf_name.replace("-", "_")
						pattern = "url(r'^%s/$', '%s.views.navigation', {\"url\":\"%s\"}, name=\"%s_%s\")," % (url_1_3, self.APPNAME, url_1_2, self.APPNAME, url_1_3)
						print pattern
			except:
				pass




# ==================================================#
#	Testing
# ==================================================#
class Test(ConvertToDjango):
	def test(self):
		attributes = ["href", "src", "data-src", "data-src-retina"]
		for att in attributes:
			print att




# ==================================================#
#	Main
# ==================================================#
def run(action):

	actions = ["convert","urlconf","transfer","restore","test"]
	if action not in actions:
		print "Must enter 1 of the following actions to execute: convert, urlconf, transfer, restore, or test."
	elif action == "convert":
		ConvertToDjango().convert()
	elif action == "urlconf":
		CreateURLCONF().create_from_links()
	elif action == "transfer":
		TransferTemplateFiles().transfer_files()
	elif action == "restore":
		RestoreTemplateFiles().restore_files()
	else:
		Test().test()
	

run("restore")






# compile_templates = ConvertToDjango()
# compile_templates.run()

# transfer_templates = TransferTemplateFiles()
# transfer_templates.run()

# i = InitVariables()
# i.get_templates(i.TEMPLATE_TRANSFER)

# urls = CreateURLCONF()
# urls.create_urls()

# RestoreTemplateFiles().restore_files()










