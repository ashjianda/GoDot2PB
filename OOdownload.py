#!/usr/bin/env python3
#
# Copyright (C) 2023 Jonathan A. Poritz
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
import argparse
import fileinput
import os
import re
import sys
import time
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Downloads PB html files from an OO OER, also building a manifest file in the style of what OOupload.py requires. Note: expects chapter titles to have either the form "Chapter <num>: <text>" or "Chapter <num> <text>".')
parser.add_argument("credentials_file", help='file with login credentials and URL for PB book; if missing, uses "credentials"', nargs="?", default="credentials", type=argparse.FileType('r'))
parser.add_argument("-m", "--manifest", help='filename for manifest to be constructred; default is "manifest_download".', default="manifest_download")
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "download.log".', default="download.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-c', '--css', help='get any custom CSS, to be stored in a file "custom.css" in the output directory; default is not to get custom CSS', action='store_true')
parser.add_argument('-n', '--not_numbered', help='when present, indicates that the chapters and sections in the PB book are not numbered and must just be considered strings; default is to assume chapters and sections are numbered according to OO style', action='store_true')
parser.add_argument("-o", "--output", help='Name to use as output directory; default is "PBhtml"', default="PBhtml")
args = parser.parse_args()
output = args.output
verbose = args.verbose
browser = None
manifest_fh = None
non = args.not_numbered
args.logfile.write("------------------------------------\n")
def log_and_print(s):
  t=time.strftime('%H:%M:%S')+" "+s
  args.logfile.write(t+"\n")
  if verbose:
    print(t)
when_work = "On "+time.strftime('%d/%m/%Y')
log_and_print(when_work+", doing ")
what_work = ' '.join(sys.argv)+" in directory "+os.getcwd()
log_and_print(what_work)
def close_exit(error_message):
  if error_message:
    log_and_print("Unsuccessful exit (on "+time.strftime('%d/%m/%Y')+")!")
  else:
    log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
  args.logfile.write("------------------------------------\n")
  args.logfile.close()
  if manifest_fh:
    manifest_fh.close()
  if browser:
    browser.close()
  args.credentials_file.close()
  if error_message:
    raise ValueError(error_message)
  quit()
def readcl():
  while True:
    r = args.credentials_file.readline()
    if not r or r[0]!="#":
      return(r)
cline = readcl()
if cline[:18] != 'URL root: https://' and cline[:17] != 'URL root: http://':
  close_exit("Credentials file does not begin with a well-formed root URL")
PB_url_root = cline[10:].strip()
if PB_url_root[-1] != '/':
  PB_url_root += '/'
log_and_print('Downloading from PB at URL: '+PB_url_root)
cline = readcl()
if cline[:14] != 'Account Name: ':
  close_exit("Credentials file does not have valid Account Name line")
PB_account_name = cline[14:].strip()
log_and_print('Using account: '+PB_account_name)
cline = readcl()
if cline[:10] != 'Password: ':
  close_exit("Credentials file does not have valid Password line")
PB_password = cline[10:].strip()
log_and_print('Got account password from credentials file')
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
opts = Options()
opts.headless = True
browser=Firefox(options=opts)
log_and_print("Opening PB login page")
browser.get(PB_url_root+'wp-login.php')
login_name = browser.find_element_by_id('user_login')
login_name.send_keys(PB_account_name)
password = browser.find_element_by_id('user_pass')
password.send_keys(PB_password)
login_button = browser.find_element_by_id('wp-submit')
log_and_print(f"Login with account '{PB_account_name}', password '{'*'*len(PB_password)}'")
login_button.click()
next_page=browser.title
if next_page[:6]=='Log In':
  browser.close()
  close_exit("Login unsuccessful")
log_and_print("Login successful")
if output[-1]=='/':
  output = output[:-1]
os.mkdir(output)
log_and_print(f'Made directory: {output}')
output += "/"
manifest_fh = open(output+args.manifest, 'w')
manifest_fh.write("# "+when_work+", this was\n")
manifest_fh.write("# "+what_work+" which resulted in this file\n")
if args.css:
  css_filename = output+"custom.css"
  css_fh = open(css_filename, "w")
  log_and_print(f"Putting custom CSS into '{css_filename}'")
  log_and_print("Going to PB custom CSS page")
  browser.get(PB_url_root+'wp-admin/themes.php?page=pb_custom_styles')
  cust_style_area = browser.find_element_by_name("your_styles")
  custom_css = cust_style_area.get_attribute("innerHTML")
  css_fh.write(custom_css)
  if custom_css[-1] != "\n":
    css_fh.write("\n")
  css_fh.close()
  ml = "CSS: "+css_filename
  manifest_fh.write(ml+"\n")
  log_and_print(f'Downloaded custom CSS; manifest block was:\n->\n{ml}\n<-')
needs_text_click = True
def get_front_back(elmnt_id, mani_code, which_matter,ntc):
  log_and_print(f"Going to {PB_url_root}wp-admin/admin.php?page=pb_organize to get {which_matter}")
  browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
  xmt = browser.find_element_by_id(elmnt_id)
  xm_sections = xmt.find_elements_by_class_name("row-title")
  xms_filenames = []
  xms_links = []
  xms_mls = []
  for xms in xm_sections:
    xms_title = xms.text
    xms_filename = xms_title.replace(" ","_")+".html"
    xms_ml = mani_code+xms_title+"\n"+output+xms_filename
    manifest_fh.write(xms_ml+"\n")
    xms_filenames.append(xms_filename)
    xms_links.append(xms.find_element_by_tag_name("a").get_attribute("href"))
    xms_mls.append(xms_ml)
    if verbose:
      print(f"Prepped {which_matter} section {xms_title}")
  for f, l, m in zip(xms_filenames, xms_links, xms_mls):
    xms_fh=open(output+f,"w")
    browser.get(l)
    if ntc:
      text_button=browser.find_element_by_id("content-html")
      ntc = False
      log_and_print('Clicked for HTML editing.')
      text_button.click()
    content=browser.find_element_by_name("content")
    xms_fh.write(content.get_attribute("value"))
    xms_fh.close()
    log_and_print(f'Downloaded {which_matter} section from {l} with manifest block:\n->\n{m}\n<-')
  return ntc
needs_text_click = get_front_back("front-matter","FM: ","frontmatter", needs_text_click)
needs_text_click = get_front_back("back-matter","BM: ", "backmatter", needs_text_click)
log_and_print(f"Going to {PB_url_root}wp-admin/admin.php?page=pb_organize to process chapters")
browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
parts=browser.find_elements_by_tag_name("h2")
if parts[0].text != "Front Matter":
  close_exit(f'Something weird about this PB: first part-link division is "{parts[0].text}" instead of "Front Matter"')
if parts[-1].text != "Back Matter":
  close_exit(f'Something weird about this PB: lasst part-link division is "{parts[-1].text}" instead of "Back Matter"')
start_core = 1
if parts[1].text == "Main Body":
  start_core = 2
core_chapters = [x.find_element_by_xpath("..") for x in parts[start_core:-1]]
manifest_chaps_s =""
chap_title_cpat = re.compile("Chapter ([1-9][0-9]*): ")
chap_title_ncpat = re.compile("Chapter ([1-9][0-9]*) ")
chap_filenames = []
chap_links = []
chap_mls = []
chaps_count = 0
for c in core_chapters:
  chap_links.append(c.find_element_by_class_name("part-actions").find_element_by_tag_name("a").get_attribute("href"))
  chapter_title=c.find_element_by_tag_name("h2").text
  if non:
    chaps_count += 1
    chap_no_s = str(chaps_count)
  else:
    mc = chap_title_cpat.match(chapter_title)
    mnc = chap_title_ncpat.match(chapter_title)
    if mc:
      chap_no_s = mc.group(1)
    elif mnc:
      chap_no_s = mnc.group(1)
    else:
      close_exit(f'Something weird about this PB: malformed part title "{chapter_title}"')
  chap_fn=chap_no_s+".0.html"
  chap_filenames.append(chap_fn)
  ml = "Part: "+chapter_title+"\n"+output+chap_fn
  chap_mls.append(ml)
  manifest_fh.write(ml+"\n")
  log_and_print(f"Wrote manifest block\n->\n{ml}\n<-")
  chap_sections = c.find_elements_by_class_name("row-title")
  sects_count = 0
  for y in chap_sections:
    chap_links.append(y.find_element_by_tag_name("a").get_attribute("href"))
    chap_sect_title = y.find_element_by_tag_name("a").text
    if non:
      sects_count +=1
      chap_sect_fn = chap_no_s+"."+str(sects_count)+".html"
    else:
      chap_sect_fn = chap_sect_title[:chap_sect_title.index(" ")]+".html"
    chap_filenames.append(chap_sect_fn)
    ml = "Chapter["+chap_no_s+"]: "+chap_sect_title+"\n"+output+chap_sect_fn
    chap_mls.append(ml)
    manifest_chaps_s += ml+"\n"
for f, l, m in zip(chap_filenames, chap_links, chap_mls):
  chap_fh=open(output+f,"w")
  browser.get(l)
  if needs_text_click:
    text_button=browser.find_element_by_id("content-html")
    needs_text_click = False
    log_and_print('Clicked for HTML editing.')
    text_button.click()
  content=browser.find_element_by_name("content")
  chap_fh.write(content.get_attribute("value"))
  chap_fh.close()
  log_and_print(f'Downloaded chapter content from {l}, manifest block:\n->\n{m}\n<-')
manifest_fh.write(manifest_chaps_s)
log_and_print("Finished writing manifest")
close_exit("")
