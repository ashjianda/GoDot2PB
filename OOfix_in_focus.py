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
import argparse
import fileinput
import os
import re
import sys
import time
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Fix "In Focus" boxes in html files prepared by OOsplit.py so they use PB textboxe.')
parser.add_argument("manifest", help="manifest as produced by OOsplit.py: should be the entire thing, including all of the Part declarations.", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "fix_in_focus.log".', default="fix_in_focus.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-s', '--start_from', help="skip all lines of the manifest up through the first one whose content title contains the given string", default='')
parser.add_argument('-u', '--updating_manifest', help='filename of new manifest which can be used with OOreup.py to correct the in focus boxes in the PB book; dafault is "manifest.update_in_focus"', default='manifest.update_in_focus')
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
pat = re.compile('<h[1-5]>[1-9][0-9]*(\.[1-9][0-9]*)+ In Focus:')
in_focus_fixed = 0
for fn in files2fix:
  new_fh = open(fn,"r+")
  old_contents = new_fh.readlines()
  new_fh.seek(0)
  in_focus_this_file = 0
  i = 0
  while i<len(old_contents)-3:
    if old_contents[i]=="<table>\n" and old_contents[i+1]=="<tr>\n" and old_contents[i+2]=="<td>\n" and pat.match(old_contents[i+3]):
      in_focus_this_file += 1
      new_fh.write('<div class="textbox textbox--key-takeaways"><header class="textbox__header">\n')
      new_fh.write(old_contents[i+3])
      in_focus_name = old_contents[i+3]
      i += 4
      if i>=len(old_contents):
        raise ValueError(f'Malformed In Focus with title "{in_focus_name}" in file {fn}')
      if old_contents[i][:3]=="<p>":
        new_fh.write(old_contents[i])
        i +=1
      if i+3>=len(old_contents) or old_contents[i]!="</td>\n" or old_contents[i+1]!="</tr>\n" or old_contents[i+2]!="<tr>\n" or old_contents[i+3]!="<td>\n":
        raise ValueError(f'Malformed In Focus with title "{in_focus_name}" in file {fn}')
      i += 4
      new_fh.write('</header>\n<div class="textbox__content">\n')
      table_depth = 0
      while i<len(old_contents):
        if not table_depth:
          if old_contents[i]=="</table>\n" or old_contents[i]=="</tr>\n" or old_contents[i]=="<tr>\n" or old_contents[i]=="<td>\n" or old_contents[i]=="<th>\n" or old_contents[i]=="</th>\n":
            raise ValueError(f'Malformed In Focus with title "{in_focus_name}" in file {fn}')
          if old_contents[i]=="</td>\n":
            if i>=len(old_contents)-2 or old_contents[i+1]!="</tr>\n" or old_contents[i+2]!="</table>\n":
              raise ValueError(f'Malformed In Focus with title "{in_focus_name}" in file {fn}')
            new_fh.write('</div>\n</div>\n')
            i += 3
            break
        if old_contents[i]=="<table>\n":
          table_depth += 1
        if old_contents[i]=="</table>\n":
          table_depth -= 1
        new_fh.write(old_contents[i])
        i += 1
      else:
        raise ValueError(f'Malformed In Focus with title "{in_focus_name}" in file {fn}')
    else:
      new_fh.write(old_contents[i])
      i += 1
  while i<len(old_contents):
    new_fh.write(old_contents[i])
    i += 1
  if in_focus_this_file:
    if not update_fh:
      update_fh = open(args.updating_manifest,"w")
      update_fh.write("# "+when_work+", this was\n")
      update_fh.write("# "+what_work+" which resulted in this file\n")
    update_fh.write(file_mls[fn])
    if args.backup_changed_files:
      old_fh = open(fn+"~","w")
      for l in old_contents:
        old_fh.write(l)
      old_fh.close()
    in_focus_fixed += in_focus_this_file
if in_focus_fixed:
  log_and_print(f'Fixed {in_focus_fixed} In Focus boxes in {len(files2fix)} files')
  update_fh.close()
else:
  log_and_print("No In Focus boxes needed fixing!")
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
