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
import code
import time
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Uploads glossary terms to PB as specified by a glossary manifest file which consists of a pair of lines for each term, the first being "GL[<post id>]: <term>" (where the post id has no meaning in the current context and can therefore be any integer) and the second just containing the filename where the HTML for the term\'s definition can be found.')
parser.add_argument("manifest", help="Filename of manifest", type=argparse.FileType('r'))
parser.add_argument("-c","--credentials_file", help="file with login credentials and URL for PB book; default is 'credentials'", default="credentials", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "gloss_up.log".', default="gloss_up.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
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
mline_no = 0
browser = None
def readml():
  global mline_no
  while True:
    mline_no += 1
    r = args.manifest.readline().strip()
    if not r or r[0]!="#":
      return(r)
def close_exit(error_message):
  if error_message:
    log_and_print("Unsuccessful exit (on "+time.strftime('%d/%m/%Y')+")!")
  else:
    log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
  args.logfile.write("------------------------------------\n")
  args.logfile.close()
  args.manifest.close()
  args.credentials_file.close()
  if browser:
    browser.close()
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
log_and_print(f'Uploading to PB at URL: {PB_url_root}')
cline = readcl()
if cline[:14] != 'Account Name: ':
  close_exit("Credentials file does not have valid Account Name line")
PB_account_name = cline[14:].strip()
log_and_print(f'Using account: {PB_account_name}')
cline = readcl()
if cline[:10] != 'Password: ':
  close_exit("Credentials file does not have valid Password line")
PB_password = cline[10:].strip()
log_and_print('Got account password from credentials file')
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.select import Select
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
  close_exit("Login unsuccessful")
log_and_print("Login successful")
term_count = 0
parens_contents = re.compile(r'[^(]*\(([^)]*)\).*')
bracket_contents = re.compile(r'[^[]*\[([1-9][0-9]*)\].*')
mline = readml()
while not start_from in mline:
  log_and_print(f'Skipping line {mline}')
  if not readml():
    close_exit(f"Malformed manfiest file: no filename on line {mline_no} for manifest content line {mline}")
  mline = readml()
  if not mline:
    log_and_print(f'No manifest lines to process after skipping to start_from of "{start_from}"')
    close_exit("")
text_button = None
while mline[:3]=='GL[':
  term=mline[mline.find("]: ")+3:]
  term_filename = readml()
  if not term_filename:
    close_exit("Malformed manfiest file: no term filename on line {mline_no}")
  log_and_print(f"defining '{term}' from file '{term_filename}'")
  def_fh = open(term_filename, "r")
  browser.get(f"{PB_url_root}/wp-admin/post-new.php?post_type=glossary")
  title_area = browser.find_element_by_id('title')
  title_area.send_keys(term)
  if not text_button:
    text_button = browser.find_element_by_id('content-html')
    text_button.click()
  content_area = browser.find_element_by_id('content')
  for def_line in def_fh:
    content_area.send_keys(def_line)
  if len(def_line) and def_line[-1]!="\n":
    content_area.send_keys("\n")
  def_fh.close()
  create_button = browser.find_element_by_id('publish')
  create_button.click()
  log_and_print(f"defined '{term}' from file '{term_filename}'")
  mline = readml()
close_exit("")
