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
import code
import os
import re
import sys
import time
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Re-uploads PB html files from an OO OER as specified in a manifest file in the format used by OOupload and OOdownload, although actually this program ignores whether a section is specified as being in the Front Matter, Back Matter, or an interior part, and ignores part numbers if given; section titles must match their PB versions exactly and must be unique (easy since usually they include numbers). Will reupload custom CSS if it is in the manifest file.')
parser.add_argument("manifest", nargs='?', default=sys.stdin, help="File containing manifest of files to re-uploaded to PB; if not present, reads from stdin", type=argparse.FileType('r'))
parser.add_argument("-c","--credentials_file", help="file with login credentials and URL for PB book; default is 'credentials'", default="credentials", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "reupload.log".', default="reupload.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-d', '--deactivate', help="removes all glossary activation short codes in the uploaded HTML", action='store_true')
parser.add_argument('-s', '--start_from', help="skip all lines of the manifest up through the first one whose content title contains the given string", default='')
args = parser.parse_args()
verbose = args.verbose
start_from = args.start_from
args.logfile.write("------------------------------------\n")
def log_and_print(s):
  t=time.strftime('%H:%M:%S')+" "+s
  args.logfile.write(t+"\n")
  if verbose:
    print(t)
log_and_print("On "+time.strftime('%d/%m/%Y')+", doing ")
log_and_print(' '.join(sys.argv)+" in directory "+os.getcwd())
def readcl(fh):
  while True:
    r = fh.readline()
    if not r or r[0]!="#":
      return(r)
cline = readcl(args.credentials_file)
if cline[:18] != 'URL root: https://' and cline[:17] != 'URL root: http://':
  raise ValueError("Credentials file does not begin with a well-formed root URL")
PB_url_root = cline[10:].strip()
if PB_url_root[-1] != '/':
  PB_url_root += '/'
log_and_print(f'Downloading from PB at URL: {PB_url_root}')
cline = readcl(args.credentials_file)
if cline[:14] != 'Account Name: ':
  raise ValueError("Credentials file does not have valid Account Name line")
PB_account_name = cline[14:].strip()
log_and_print(f'Using account: {PB_account_name}')
cline = readcl(args.credentials_file)
if cline[:10] != 'Password: ':
  raise ValueError("Credentials file does not have valid Password line")
PB_password = cline[10:].strip()
log_and_print('Got account password from credentials file')
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
opts = Options()
opts.headless = True
browser=Firefox(options=opts)
log_and_print('Opening PB login page')
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
  raise ValueError("Login unsuccessful")
log_and_print("Login successful")
log_and_print(f"Going to PB Organize page {PB_url_root}wp-admin/admin.php?page=pb_organize")
browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
sections2reup = 0
parts=browser.find_elements_by_tag_name("h2")
atags = browser.find_elements_by_tag_name("a")
section_info = {}
css_filename = ''
mf_section_line = re.compile("Chapter\[[1-9][0-9]*\]: (.*)")
while True:
  mline = readcl(args.manifest)
  if not mline:
    break
  if mline[:5]=="CSS: ":
    if start_from and not start_from in mline:
      continue
    start_from = ''
    css_filename = mline[5:]
    if not css_filename:
      raise ValueError("Malformed manifest file: no custom CSS filename")
    continue
  if start_from and not start_from in mline:
    if not readcl(args.manifest):
      raise ValueError(f"Malformed manifest file: no filename for content line {mline}")
    continue
  start_from = ''
  is_part = False
  if mline[:4]=="FM: " or mline[:4]=="BM: ":
    section_name = mline[4:-1]
  elif mline[:6]=="Part: ":
    is_part = True
    section_name = mline[6:-1]
  elif mf_section_line.match(mline):
    section_name = mf_section_line.sub("\\1",mline[:-1])
  else:
    raise ValueError("Malformed manifest file with line: "+mline)
  if section_name in section_info:
    raise ValueError(f'Malformed manifest file: section name "{section_name}" appears more than once!')
  fn = readcl(args.manifest).strip()
  if not fn:
    raise ValueError("Malformed manifest file with no filename specified for line: "+mline)
  section_fh = open(fn,"r")
  section_element = None
  if is_part:
    for p in parts:
      if p.text == section_name:
        section_element = p.parent.find_element_by_class_name("part-actions").find_element_by_tag_name("a")
        break
  else:
    for a in atags:
      if a.text==section_name:
        section_element=a
        break
  if not section_element:
    raise ValueError(f'Section with name {section_name} not found in PB book.')
  section_url = section_element.get_attribute('href')
  section_info[section_name] = [section_fh, section_url]
  sections2reup += 1
args.manifest.close()
from selenium.webdriver.common.keys import Keys
if css_filename:
  log_and_print('Will reupload custom CSS')
  css_fh = open(css_filename, "r")
  log_and_print(f"Getting custom CSS from file '{css_filename}'")
  log_and_print(f"Going to PB custom CSS page {PB_url_root}wp-admin/themes.php?page=pb_custom_styles")
  browser.get(PB_url_root+'wp-admin/themes.php?page=pb_custom_styles')
  cust_style_area = browser.find_element_by_xpath("/html/body/div/div[2]/div[2]/div[1]/div[2]/div/form/div[3]/div[1]/textarea")
  browser.execute_script("window.scrollTo(70,500)")
  cust_style_area.click()
  cust_style_area.send_keys(Keys.CONTROL+"a")
  cust_style_area.send_keys(Keys.DELETE)
  for css_line in css_fh:
    cust_style_area.send_keys(css_line)
  if len(css_line) and css_line[-1]!="\n":
    cust_style_area.send_keys("\n")
  css_fh.close()
  save_button = browser.find_element_by_id('save')
  save_button.click()
  log_and_print("Successfully reuploaded custom CSS")
if sections2reup==1:
  log_and_print('Found URL and new content file to reupload 1 section')
else:
  log_and_print(f'Found URLs and new content files to reupload {str(sections2reup)} sections')
needs_text_click = True
sections_handled = 0
start_gloss_pat = re.compile(r'\[pb_glossary id="[1-9][0-9]*"\]')
end_gloss_pat = re.compile(r'\[/pb_glossary\]')
glossaries_found = 0
for s in section_info:
  browser.get(section_info[s][1])
  if needs_text_click:
    text_button=browser.find_element_by_id("content-html")
    needs_text_click = False
    log_and_print('Clicked for HTML editing.')
    text_button.click()
  content=browser.find_element_by_name("content")
  content.click()
  content.send_keys(Keys.CONTROL+"a")
  content.send_keys(Keys.DELETE)
  for l in section_info[s][0]:
    if args.deactivate:
      (l, gn) = end_gloss_pat.subn('', start_gloss_pat.sub('', l))
      glossaries_found += gn
    content.send_keys(l)
  section_info[s][0].close()
  save_button = browser.find_element_by_id('publish')
  save_button.click()
  log_and_print(f"Saved new version of section {s}")
  sections_handled += 1
if sections_handled==1:
  log_and_print('Reuploaded 1 section')
else:
  log_and_print(f'Reuploaded {str(sections_handled)} sections')
if args.deactivate:
  if glossaries_found==1:
    log_and_print('Deactivated 1 glossary reference.')
  else:
    log_and_print(f'Deactivated  {str(glossaries_found)} glossary references')
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
