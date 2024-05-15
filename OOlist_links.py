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
import code
from bs4 import BeautifulSoup
import requests
import argparse
import fileinput
import random
import os
import re
import sys
import time
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='list external links in html files prepared by OOsplit.py or OOdownload.py')
parser.add_argument("manifest", nargs='?', default=sys.stdin, help="manifest as produced by OOsplit.py or OOdownload.py; if not present, reads from stdin", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "list_links.log".', default="list_links.log")
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-c', '--context', help="print some context for each link listed", action='store_true')
parser.add_argument('-s', '--start_from', help="skip all lines of the manifest up through the first one whose content title contains the given string", default='')
parser.add_argument('-n', '--no_test_urls', help="do not test if the external URLs seem to be live; default: false", action='store_true')
args = parser.parse_args()
verbose = args.verbose
context = args.context
no_test_urls = args.no_test_urls
start_from = args.start_from
logfile_fh = open(args.logfile,"a")
logfile_fh.write("------------------------------------\n")
def log_and_print(s):
  logfile_fh.write(s+"\n")
  if verbose:
    print(s)
log_and_print("On "+time.strftime('%d/%m/%Y')+", at "+time.strftime('%H:%M:%S')+", doing ")
log_and_print(' '.join(sys.argv)+" in directory "+os.getcwd())
def readml():
  while True:
    r = args.manifest.readline()
    if not r or r[0]!="#":
      return(r)
files2examine = []
file_mls = {}
urls_found = {}
bad_urls_found = []
good_ext_links = 0
bad_ext_links = 0
all_ext_links = 0
num_int_links = 0
image_links = 0
user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]
while True:
  mline = readml()
  if not mline:
    break
  if mline[:5]=="CSS: ":
    if start_from and not start_from in mline:
      continue
    start_from = ''
    continue
  fnnl = readml()
  fn = fnnl.strip()
  if not fn:
    raise ValueError(f"Malformed manifest file: no filename for content line {mline}")
  if start_from and not start_from in mline:
    continue
  start_from = ''
  file_mls[fn] = mline+fnnl
  files2examine.append(fn)
for fn in files2examine:
  file_good_ext_links = 0
  file_bad_ext_links = 0
  file_all_ext_links = 0
  file_int_links = []
  file_int_links_texts = []
  file_int_links_contexts = []
  title=file_mls[fn][:file_mls[fn].index("\n")]
  log_and_print(f'\n{"-"*(len(title)+2)}\n|{title}|\n{"-"*(max(len(title),len(fn))+2)}\n|{fn}|\n{"-"*(len(fn)+2)}')
  new_fh = open(fn,"r")
  new_soup = BeautifulSoup(new_fh)
  links = new_soup.find_all("a", href=True)
  for l in links:
    t = l.get_text()
    if l.img:
      t += '\nIMG: SRC: "'+l.img.get("src")+'"\nIMG ALT: "'+l.img.get("alt")+'"'
      image_links += 1
    u = l.get("href")
    c = "CONTEXT: "+l.parent.text+"\n"
    if u[0]=="#":
      file_int_links.append(u)
      file_int_links_texts.append(t)
      file_int_links_contexts.append(c)
      continue
    if no_test_urls:
      file_all_ext_links += 1
      log_and_print(f'{c*context}TEXT: {t}\nURL: {u}\n')
    else:
      if u in urls_found:
        u_good = urls_found[u]
      else:
        user_agent = random.choice(user_agent_list)
        headers = {'User-Agent': user_agent}
        try:
          res = requests.head(u, timeout=30, headers=headers)
        except:
          u_good = False
        else:
          u_good = res.ok
        urls_found[u] = u_good
        if not u_good:
          bad_urls_found.append(u)
      file_good_ext_links += u_good
      file_bad_ext_links += 1-u_good
      log_and_print(f'{c*context}TEXT: {t}\nURL {u_good*"ok"}{(1-u_good)*"BAD"}: {u}\n')
  if no_test_urls:
    log_and_print(f'Found {file_all_ext_links} external link{"s"*(file_all_ext_links != 1)} in this file\n')
  else:
    log_and_print(f'Found {file_good_ext_links} good and {file_bad_ext_links} bad external links in this file\n')
  all_ext_links += file_all_ext_links
  good_ext_links += file_good_ext_links
  bad_ext_links += file_bad_ext_links
  if file_int_links:
    for u,t,c in zip(file_int_links,file_int_links_texts,file_int_links_contexts):
      log_and_print(f'{c*context}{t}\n-->\n{u}\n')
    if len(file_int_links)>1:
      log_and_print(f"There were {len(file_int_links)} internal links in this file\n")
    else:
      log_and_print("There was an internal link in this file\n")
    num_int_links += len(file_int_links)
log_and_print(f'\n\n------------------------------------\nExamined {len(files2examine)} files')
if no_test_urls:
  log_and_print(f'Found {all_ext_links} external links')
else:
  log_and_print(f'Found {good_ext_links} good and {bad_ext_links} bad external links')
  if bad_ext_links:
    log_and_print('These URLS had problems:')
    for l in bad_urls_found:
      log_and_print(f' {l}')
log_and_print(f'Found {num_int_links} internal link{"s"*(num_int_links != 1)}')
log_and_print(f'Found {image_links} link{"s"*(image_links != 1)} attached to images')
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+" at "+time.strftime('%H:%M:%S')+")!")
logfile_fh.write("------------------------------------\n")
logfile_fh.close()
args.manifest.close()
