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
import code
import re
import sys
import time
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Downloads PB glossary terms from an OO OER, making a glossary manifest file, consisting of a pair of lines for each term, the first being "GL[<post_id>]: <term>" and the second just containing the filename indicating where the HTML for the term\'s definition can be found.')
parser.add_argument("credentials_file", help='file with login credentials and URL for PB book; if missing, uses "credentials"', nargs="?", default="credentials", type=argparse.FileType('r'))
parser.add_argument("-m", "--manifest", help='filename for manifest to be made inside the output directory; default is "manifest_glossary".', default="manifest_glossary")
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "gloss_down.log".', default="gloss_down.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument("-o", "--output", help='Name of directory where manifest and HTML files will be placed; default is "PBglossary"', default="PBglossary")
args = parser.parse_args()
output = args.output
verbose = args.verbose
browser = None
manifest_fh = None
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
  close_exit("Credentials file does not have valid Account Name cline")
PB_account_name = cline[14:].strip()
log_and_print('Using account: '+PB_account_name)
cline = readcl()
if cline[:10] != 'Password: ':
  close_exit("Credentials file does not have valid Password cline")
PB_password = cline[10:].strip()
log_and_print('Got account password from credentials file')
args.credentials_file.close()
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
  close_exit("Login unsuccessful")
log_and_print("Login successful")
if output[-1]=='/':
  output = out[:-1]
os.mkdir(output)
log_and_print(f'Made directory: {output}')
output += "/"
manifest_fh = open(output+args.manifest, "w")
manifest_fh.write("# "+when_work+", this was\n")
manifest_fh.write("# "+what_work+" which resulted in this file\n")
terms = []
edit_links = []
post_ids = []
page_no = 1
browser.get(f"{PB_url_root}/wp-admin/edit.php?post_type=glossary&mode=list")
while True:
  log_and_print(f"working on glossary list at URL: {browser.current_url}")
  rts = browser.find_elements_by_class_name("row-title")
  for r in rts:
    terms.append(r.text)
    l=r.get_attribute("href")
    edit_links.append(l)
    post_ids.append(l[l.find("post=")+5:l.find("&action")])
  npb = browser.find_elements_by_class_name("next-page")
  if not npb:
    break
  page_no += 1
  browser.get(f"{PB_url_root}/wp-admin/edit.php?post_type=glossary&mode=list&paged={page_no}")
term_count = 0
for t, l, i in zip(terms, edit_links, post_ids):
  manifest_fh.write(f"GL[{i}]: {t}\n{output}{str(term_count)}\n")
  browser.get(l)
  ta = browser.find_element_by_tag_name("textarea")
  definition = ta.get_attribute("innerHTML")
  def_fh = open(output+str(term_count),"w")
  def_fh.write(definition)
  def_fh.close()
  log_and_print(f'file "{output+str(term_count)}" has def of glossary item: {t}')
  term_count += 1
if term_count:
  log_and_print(f"Successfully downloaded definitions for {term_count} terms")
else:
  log_and_print("There were no glossary terms to download!")
close_exit("")
