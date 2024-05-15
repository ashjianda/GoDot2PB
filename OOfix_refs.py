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
parser = argparse.ArgumentParser(description='Fix paragraphs in <h1> Reference sections to having hanging indent.')
parser.add_argument("manifest", help="manifest as produced by OOsplit.py: must be the entire thing, including all of the Part declarations!", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "fix_refs.log".', default="fix_refs.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-s', '--start_from', help="skip all lines of the manifest up through the first one whose content title contains the given string", default='')
parser.add_argument('-u', '--updating_manifest', help='filename of new manifest which can be used with OOreup.py to correct the refs in the PB book; dafault is "manifest.update_refs"', default='manifest.update_refs')
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
files2fix = []
file_mls = {}
update_fh = None
def readml():
  while True:
    r = args.manifest.readline()
    if not r or r[0]!="#":
      return(r)
while True:
  mline = realml()
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
refs2fix = 0
files_with_ref_sections = 0
ref_head_pat = re.compile(r'<h1>[1-9][0-9]*.[1-9][0-9]*.[1-9][0-9]* References</h1>')
for fn in files2fix:
  new_fh = open(fn,"r+")
  old_contents = new_fh.read()
  new_contents = ""
  in_refs = False
  got_refs = False
  fixes_this_file = 0
  file_line_no = 0
  for l in old_contents.split("\n"):
    file_line_no += 1
    if not l.strip():
      new_contents += l+"\n"
      continue
    if in_refs:
      if l[:3]=="<p>":
        if l[-4:]!="</p>":
          raise ValueError(f"Expecting '<p>...</p>' to be one line,\ninstead got '{l}'\nin file {fn}\non line number {file_line_no}")
        fixes_this_file += 1
        new_contents += '<p class="hanging-indent">'+l[3:]+'\n'
        continue
      if l[:26]=='<p class="hanging-indent">':
        new_contents += l+"\n"
        continue
      if l[:10]=='<a id="fig':
        new_contents += l+"\n"
        in_refs = False
        continue
      raise ValueError(f"Unexpected contents of References subsection\ngot '{l}'\nin file {fn}\non line number {file_line_no}")
    if ref_head_pat.match(l):
      if got_refs:
        raise ValueError(f"Unexpected second References header:\ngot '{l}'\nin file {fn}\non line number {file_line_no}")
      in_refs = True
      got_refs = True
    new_contents += l+"\n"
    continue
  if got_refs:
    files_with_ref_sections += 1
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
    refs2fix += fixes_this_file
    new_fh.seek(0)
    new_fh.write(new_contents)
    new_fh.truncate()
    new_fh.close()
if refs2fix:
  log_and_print(f'Fixed {refs2fix} references in {files_with_ref_sections} References sections from {len(files2fix)} files')
  update_fh.close()
else:
  log_and_print("No references needed fixing!")
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
