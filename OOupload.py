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
parser = argparse.ArgumentParser(description='Uploads to PB html files which came from GD and were customized for that purpose, as specified by a manifest file with the following format:\n-----------------------------\nCSS: <filename of source for custom CSS>\nFM: <title of front matter section>\n<filename of source for that front matter section>\nBM: <title of back matter section>\n<filename of source for that back matter section>\nPart: <title of part>\n<filename of source for that part>\nChapter[<part # for chapter>]: <title of chapter>\n<filename of source for that chapter>\n-----------------------------\nNotes:\n  - CSS line should appear zero or one times\n  - FM, BM, Part, and Chapter lines in manifest should appear 0 or more times in like blocks, in the order shown above\n  - Sections, parts, and chapters will be in PB in the order they appear in the manifest\n  - Part number starts at 1\n  - Should always include Part lines for all of the chapters in the author\'s version of the book; skip past them if they don\'t need to be uploaded with the "-s" option\n\nUses credentials file with the  format:\n-----------------------------\nURL root: <text>\nAccount Name: <text>\nPassword: <text>\n-----------------------------\n',formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("manifest", nargs='?', default=sys.stdin, help="File containing manifest of files to uploaded to PB; if not present, reads from stdin", type=argparse.FileType('r'))
parser.add_argument("-c","--credentials_file", help="file with login credentials and URL for PB book; default is 'credentials'", default="credentials", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "upload.log".', default="upload.log", type=argparse.FileType('a'))
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
def readml():
  global mline_no
  while True:
    mline_no += 1
    r = args.manifest.readline().strip()
    if not r or r[0]!="#":
      return(r)
mline = readml()
while not start_from in mline:
  log_and_print(f'Skipping line {mline}')
  if mline[:5] != "CSS: " and not readml():
    raise ValueError(f"Malformed manfiest file: no filename on line {mline_no} for manifest content line {mline}")
  mline = readml()
  if not mline:
    log_and_print(f'No manifest lines to process after skipping to start_from of "{start_from}"')
    log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
    args.logfile.write("------------------------------------\n")
    args.logfile.close()
    args.manifest.close()
    quit()
def readcl():
  while True:
    r = args.credentials_file.readline()
    if not r or r[0]!="#":
      return(r)
cline = readcl()
if cline[:18] != 'URL root: https://' and cline[:17] != 'URL root: http://':
  raise ValueError("Credentials file does not begin with a well-formed root URL")
PB_url_root = cline[10:].strip()
if PB_url_root[-1] != '/':
  PB_url_root += '/'
log_and_print(f'Uploading to PB at URL: {PB_url_root}')
cline = readcl()
if cline[:14] != 'Account Name: ':
  raise ValueError("Credentials file does not have valid Account Name line")
PB_account_name = cline[14:].strip()
log_and_print(f'Using account: {PB_account_name}')
cline = readcl()
if cline[:10] != 'Password: ':
  raise ValueError("Credentials file does not have valid Password line")
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
  browser.close()
  raise ValueError("Login unsuccessful")
log_and_print("Login successful")
fm_sec_count = 0
bm_sec_count = 0
part_count = 0
parens_contents = re.compile(r'[^(]*\(([^)]*)\).*')
bracket_contents = re.compile(r'[^[]*\[([1-9][0-9]*)\].*')
if mline[:5]=="CSS: ":
  css_filename = mline[5:]
  if not css_filename:
    raise ValueError(f"Malformed manifest file: no custom CSS filename on line {mline_no}")
  css_fh = open(css_filename, "r")
  log_and_print(f"Getting custom CSS from file '{css_filename}'")
  log_and_print(f"Going to PB custom CSS page {PB_url_root}wp-admin/themes.php?page=pb_custom_styles")
  browser.get(PB_url_root+'wp-admin/themes.php?page=pb_custom_styles')
  cust_style_area = browser.find_element_by_xpath("/html/body/div/div[2]/div[2]/div[1]/div[2]/div/form/div[3]/div[1]/textarea")
#  browser.execute_script("window.scrollTo(70,500)")
#  browser.execute_script("arguments[0].scrollIntoView();", cust_style_area)
#  cust_style_area.click()
  from selenium.webdriver.common.keys import Keys
  cust_style_area.send_keys(Keys.CONTROL+"a")
  cust_style_area.send_keys(Keys.DELETE)
  for css_line in css_fh:
    cust_style_area.send_keys(css_line)
  if len(css_line) and css_line[-1]!="\n":
    cust_style_area.send_keys("\n")
  css_fh.close()
  save_button = browser.find_element_by_id('save')
  save_button.click()
  log_and_print("Successfully saved new custom CSS")
  mline = readml()
onOrganizePage = False
text_button = None
while mline[:4]=='FM: ':
  if not onOrganizePage:
    browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
    log_and_print("Organize page opened to handle Front Matter line(s)")
    onOrganizePage = True
  fm_sec_count += 1
  fm_sec_name = mline[4:]
  fm_filename = readml()
  if not fm_filename:
    raise ValueError("Malformed manfiest file: no frontmatter section filename on line {mline_no}")
  log_and_print(f"Loading Front Matter section #{str(fm_sec_count)} {fm_sec_name} from file {fm_filename}")
  fm_sec_fh = open(fm_filename, "r")
  add_fm = browser.find_element_by_link_text("Add Front Matter")
  add_fm.click()
  title_area = browser.find_element_by_id('title')
  title_area.send_keys(fm_sec_name)
  if not text_button:
    text_button = browser.find_element_by_id('content-html')
    text_button.click()
  content_area = browser.find_element_by_id('content')
  for fm_sec_line in fm_sec_fh:
    content_area.send_keys(fm_sec_line)
  if len(fm_sec_line) and fm_sec_line[-1]!="\n":
    content_area.send_keys("\n")
  fm_sec_fh.close()
  create_button = browser.find_element_by_id('publish')
  create_button.click()
  log_and_print(f"Created Front Matter section '{fm_sec_name}'.")
  mline = readml()
while mline[:4]=='BM: ':
  if not onOrganizePage:
    browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
    log_and_print("Organize page opened to handle Back Matter line(s)")
    onOrganizePage = True
  bm_sec_count += 1
  bm_sec_name = mline[4:]
  bm_filename = readml()
  if not bm_filename:
    raise ValueError("Malformed manfiest file: no backmatter section filename on line {mline_no}")
  log_and_print(f"Loading Back Matter section #{str(bm_sec_count)} {bm_sec_name} from file {bm_filename}")
  bm_sec_fh = open(bm_filename, "r")
  add_bm = browser.find_element_by_link_text("Add Back Matter")
  add_bm.click()
  title_area = browser.find_element_by_id('title')
  title_area.send_keys(bm_sec_name)
  if not text_button:
    text_button = browser.find_element_by_id('content-html')
    text_button.click()
  content_area = browser.find_element_by_id('content')
  for bm_sec_line in bm_sec_fh:
    content_area.send_keys(bm_sec_line)
  if len(bm_sec_line) and bm_sec_line[-1]!="\n":
    content_area.send_keys("\n")
  bm_sec_fh.close()
  create_button = browser.find_element_by_id('publish')
  create_button.click()
  log_and_print(f"Created Back Matter section '{bm_sec_name}'.")
  mline = readml()
while mline[:6]=='Part: ':
  if not onOrganizePage:
    browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
    log_and_print("Organize page opened to handle Part line(s)")
    onOrganizePage = True
  part_count +=1
  part_name = mline[6:]
  part_filename = readml()
  if not part_filename:
    raise ValueError("Malformed manfiest file: no part filename on line {mline_no}")
  log_and_print(f"Loading Part #{str(part_count)} '{part_name}' from file '{part_filename}'")
  part_fh = open(part_filename, "r")
  add_part = browser.find_element_by_link_text("Add Part")
  add_part.click()
  title_area = browser.find_element_by_id('title')
  title_area.send_keys(part_name)
  if not text_button:
    text_button = browser.find_element_by_id('content-html')
    text_button.click()
  content_area = browser.find_element_by_id('content')
  for part_line in part_fh:
    content_area.send_keys(part_line)
  if len(part_line) and part_line[-1]!="\n":
    content_area.send_keys("\n")
  part_fh.close()
  create_button = browser.find_element_by_id('publish')
  create_button.click()
  log_and_print(f"Created Part '{part_name}'.")
  mline = readml()
while mline[:8]=='Chapter[':
  if not onOrganizePage:
    browser.get(PB_url_root+'wp-admin/admin.php?page=pb_organize')
    log_and_print("Organize page opened to handle Chapter line(s)")
  chapters_part = int(bracket_contents.sub(r'\1',mline))
  chapter_name = mline[mline.index(" ")+1:]
  chapter_filename = readml()
  if not chapter_filename:
    raise ValueError(f"Malformed manfiest file: no chapter filename on line {mline_no}")
  log_and_print(f"Loading Chapter '{chapter_name}' in Part #{str(chapters_part)} from file '{chapter_filename}'")
  chapter_fh = open(chapter_filename, "r")
  add_chap = browser.find_element_by_link_text("Add Chapter")
  parts=browser.find_elements_by_tag_name("h2")
  if parts[0].text != "Front Matter":
    raise ValueError(f'Something weird about this PB: first part-link division is "{parts[0].text}" instead of "Front Matter"')
  if parts[-1].text != "Back Matter":
    raise ValueError(f'Something weird about this PB: lasst part-link division is "{parts[-1].text}" instead of "Back Matter"')
  if parts[1].text == "Main Body":
    pull_down_offset = 0
  else:
    pull_down_offset = -1
  add_chap.click()
  chap_parent = browser.find_element_by_id('chapter-parent')
  chap_sel = Select(chap_parent.find_element_by_tag_name("select"))
  chap_sel.select_by_index(chapters_part+pull_down_offset)
  title_area = browser.find_element_by_id('title')
  title_area.send_keys(chapter_name)
  if not text_button:
    text_button = browser.find_element_by_id('content-html')
    text_button.click()
  content_area = browser.find_element_by_id('content')
  for chapter_line in chapter_fh:
    content_area.send_keys(chapter_line)
  if len(chapter_line) and chapter_line[-1]!="\n":
    content_area.send_keys("\n")
  chapter_fh.close()
  create_button = browser.find_element_by_id('publish')
  create_button.click()
  log_and_print(f"Created Chapter '{chapter_name}' in Part #{str(chapters_part)}.")
  mline = readml()
browser.close()
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
args.manifest.close()
