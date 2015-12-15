#*========================== #
#*  Author:		Dave Luke Jr
#*  Company:	CenterStack.io
#*  Description:	Convert to Static
#*========================== #
import os, sys, codecs, re, shutil, zipfile, urllib2, urllib
from pprint import pprint as pp
import bs4, pyautogui
sys.stdout = codecs.getwriter('utf8')(sys.stdout)



# ==================================================#
#	Variables Class
# ==================================================#
class InitVariables():
	def __init__(self):																						# Notes:
		self.PARSER				= "lxml"																	# Parser Options: html.parser, lxml, html5lib
		self.AUTHOR				= "CenterStack"																# What you want the meta.author.content tag to equal
		self.TITLE					= "CenterStack"																# What you want the meta.title.string to equal
		self.STATIC				= "{% load staticfiles %}"														# Django load statement for static files
		self.PRODUCTION			= False																	# Production or Development?
		self.APPNAME				= "metronic"																	# This is the name of the app name and folder name
		self.URL_PREFIX				= "metronic_admin_"
		self.APPDIR				= os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'apps', self.APPNAME)
		self.STATIC_DIR				= os.path.join(self.APPDIR, 'static', 'static_dirs', self.APPNAME)
		self.TEMPLATE_FOLDER		= os.path.join(self.APPDIR, "templates", self.APPNAME)									# Folder that contains all your template HTML files
		self.TEMPLATE_FILES 			= self.get_templates(self.TEMPLATE_FOLDER)											# List of template HTML files in the TEMPLATES_FOLDER
		self.TEMPLATE_BACKUP_ZIP	= "/sys/centerstack/site/scripts/convertToDjango/backups/%s.zip" % self.APPNAME				# Backup .zip file of all original template HTML files
		self.URLCONF_INDEX			= "/sys/centerstack/site/apps/metronic/templates/metronic/admin_1/index.html"									# This is the file that is used to pull the information needed to build the urlconf automatically - default is index.html


	def get_templates(self, dir):
		templates = []
		templates_fn = []
		templates_folder = []
		for root, dirs, files in os.walk(dir):
			for file in files:
				path = os.path.join(root, file)
				if file.lower().endswith('.html'):
					templates.append(path)
					templates_fn.append(file)
					templates_folder.append(os.path.basename(root))
		return templates


	def get_files(self, dir):
		files = []
		filesbase = []
		for file in os.listdir(dir):
			filename = os.path.join(dir,file)
			filenamebase = os.path.basename(os.path.join(dir,file))
			if os.path.isfile(filename):
				if filenamebase[0] != ".":
					files.append(filename)
					filesbase.append(filenamebase)
		return files


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


	def compile_src(self):

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
					self.compile_src()
					self.compile_canvas_logo()
					self.save(template_file)
					print os.path.basename(template_file)
			print "\nProcess Complete!\n"
		except Exception, e:
			print e

# ==================================================#
#	Generate URL Conf
# ==================================================#
class CreateURLS(ConvertToDjango):

	def create_urls(self):
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
#	Reload new copies of all the templates in the templates folder
# ==================================================#
class RestoreTemplateFiles(InitVariables):

	def run(self):
		response = pyautogui.confirm("Restore Template Files?") if self.PRODUCTION else "OK"
		if  response == "OK":
			try:
				shutil.rmtree(self.TEMPLATE_FOLDER)
			except:
				pass
			
			with zipfile.ZipFile(self.TEMPLATE_BACKUP_ZIP, "r") as z:
				z.extractall(os.path.join(self.TEMPLATE_FOLDER,".."))
			try:
				shutil.rmtree(os.path.join(self.TEMPLATE_FOLDER,"..","__MACOSX"))
			except:
				pass


# ==================================================#
#	Main
# ==================================================#
compile_templates = ConvertToDjango()
compile_templates.run()

# i = InitVariables()
# i.get_templates(i.TEMPLATE_FOLDER)

# urls = CreateURLS()
# urls.create_urls()

# reload_templates = RestoreTemplateFiles()
# reload_templates.run()







