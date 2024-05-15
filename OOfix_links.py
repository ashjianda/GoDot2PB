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
parser = argparse.ArgumentParser(description='Fix internal links in html files prepared by OOsplit.py so they refer to the appropriate PB URLs.')
parser.add_argument("manifest", help="manifest as produced by OOsplit.py: must be the entire thing, including all of the Part declarations!", type=argparse.FileType('r'))
parser.add_argument("-c","--credentials_file", help="file with login credentials and URL for PB book (only URL is used!); default is 'credentials'", default="credentials", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "fix_links.log".', default="fix_links.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-s', '--start_from', help="skip all lines of the manifest up through the first one whose content title contains the given string", default='')
parser.add_argument('-u', '--updating_manifest', help='filename of new manifest which can be used with OOreup.py to correct the links in the PB book; dafault is "manifest.update_links"', default='manifest.update_links')
parser.add_argument('-b', '--backup_changed_files', help='save a backup copy of the original file, in a file with the same name to which "~" is appended', action='store_true')
args = parser.parse_args()
verbose = args.verbose
start_from = args.start_from
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
files2fix = []
chap_links = {}
file_mls = {}
update_fh = None
def pb_link(s):
  t=""
  for x in s:
    if x.isalpha() or x.isdigit():
      t += x
    elif t and t[-1]!="-":
      t += "-"
  if t[-1]=="-":
    t=t[:-1]
  return(t.lower())
def readml():
  while True:
    r = args.manifest.readline()
    if not r or r[0]!="#":
      return(r)
while True:
  mline = readml()
  print(mline)
  if not mline:
    if start_from:
      log_and_print(f'No manifest lines to process after skipping to start_from of "{start_from}"')
      log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
      args.logfile.write("------------------------------------\n")
      args.logfile.close()
      args.manifest.close()
      quit()
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
  files2fix.append(fn)
  if mline[:4]=="FM: " or mline[:4]=="BM: " or mline[:8]=="Chapter[":
    continue
  if mline[:6]!="Part: ":
    raise ValueError(f'Malformed manfiest file: unrecognized line "{mline}"')
  pbl=pb_link(mline[6:])
  chap_links[mline[6:6+mline[6:].find(":")]]=pbl
  chap_links[mline[6:]]=pbl
internal_GD_link = re.compile('<a href="#[^"]+">(Chapter [1-9][0-9]*(:[^<]*)?)</a>')
def better_linking(m):
  if m.group(1) in chap_links:
    return(f'<a href="{PB_url_root}part/{chap_links[m.group(1)]}/">{m.group(1)}</a>')
  return m.group(0)
links2fix = 0
for fn in files2fix:
  new_fh = open(fn,"r+")
  old_contents = new_fh.read()
  fixes_this_file = len(internal_GD_link.findall(old_contents))
  if fixes_this_file:
    if not update_fh:
      update_fh = open(args.updating_manifest,"w")
      update_fh.write("# "+when_work+", this was\n")
      update_fh.write("# "+what_work+" which resulted in this file\n")
    update_fh.write(file_mls[fn])
    if args.backup_changed_files:
      old_fh = open(fn+"~","w")
      old_fh.write(old_contents)
      old_fh.close()
    links2fix += fixes_this_file
    new_fh.seek(0)
    new_fh.write(internal_GD_link.sub(better_linking, old_contents))
    new_fh.truncate()
    new_fh.close()
if links2fix:
  log_and_print(f'Fixed {links2fix} links in {len(files2fix)} files')
  update_fh.close()
else:
  log_and_print("No internal links needed fixing!")
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
args.manifest.close()
