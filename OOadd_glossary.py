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
parser = argparse.ArgumentParser(description='Add glossary references in html files prepared by OOsplit.py so the appropriate texts will have active PB glossary terms. Text which consists of a non-letter character followed by a term from the glossary_manifest in any case, followed by a non-letter chacter is considered "appropriate" (only the term itself is activated, not the surrounding non-letter characters).')
parser.add_argument("glossary_manifest", help="glossary manifest as produced by OOglossary_down.py, used for terms, post ids, and names of html files with glossary definitions", type=argparse.FileType('r'))
parser.add_argument("-m","--manifest", help='manifest as produced by OOsplit.py; used only for names of HTML files to process; default is "manifest"', default="manifest", type=argparse.FileType('r'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "add_glossarys.log".', default="add_glossary.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument('-a', '--activationless', help="do not activate glossary terms in headers; defaut=False", action='store_true')
parser.add_argument('-s', '--start_from', help="skip all lines of the manifest up through the first one whose content title contains the given string", default='')
parser.add_argument('-u', '--updating_manifest', help='filename of new manifest which can be used with OOreup.py to activate the glossary terms in the PB book; dafault is "manifest.add_glossary"', default='manifest.add_glossary')
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
def readcl(fh):
  while True:
    r = fh.readline()
    if not r or r[0]!="#":
      return(r)
while True:
  mline = readcl(args.manifest)
  if not mline:
    break
  if mline[:5]=="CSS: ":
    if start_from and not start_from in mline:
      continue
    start_from = ''
    continue
  fnnl = readcl(args.manifest)
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
refs_pat = re.compile("<h1>[1-9][0-9]?.[1-9][0-9]?.[1-9][0-9]? References</h1>")
LandA_pat = re.compile("<h1>[1-9][0-9]?.[1-9][0-9]?.[1-9][0-9]? Licenses and Attributions")
img_desc_pat = re.compile(r'<a id="fig[1-9][0-9]?.[1-9][0-9]?"></a><strong>Image Description')
header_pat = re.compile(r'<h[1-5]>')
terms = []
term_ids = {}
term_pats = {}
term_fixes = {}
while True:
  gline = readcl(args.glossary_manifest)
  if not gline:
    break
  gfn = readcl(args.glossary_manifest)
  if not gfn:
    raise ValueError(f"Malformed glossary manifest file: no filename for content line {gline}")
  t = gline[gline.find(":")+1:].strip()
  terms.append(t)
  id = gline[3:gline.find("]")]
  term_ids[t] = id
  pat = re.compile("("+t+")", re.IGNORECASE)
  term_pats[t] = pat
  term_fixes[t] = 0
for i in range(len(terms)):
  for j in range(len(terms)):
    if i==j:
      continue
    if term_pats[terms[i]].search(terms[j]):
      raise ValueError(f"Bad glossary: {terms[i]} conflicts with {terms[j]}")
total_fixes = 0
files_with_fixes = 0
for fn in files2fix:
  fixes_this_file = 0
  new_fh = open(fn,"r+")
  old_contents = new_fh.read()
  new_contents = ""
  new_fh.seek(0)
  no_gloss = False
  l = ""
  while True:
    new_contents += l
    l = new_fh.readline()
    if not l:
      break
    if no_gloss:
      if img_desc_pat.match(l) or (l[:4]=="<h1>" and not (refs_pat.match(l) or LandA_pat.match(l))):
        no_gloss = False
      continue
    if refs_pat.match(l) or LandA_pat.match(l):
      no_gloss = True
      continue
    if args.headless and header_pat.match(l):
      continue
    for t in terms:
      [l, n] = term_pats[t].subn(r'[pb_glossary id="'+term_ids[t]+r'"]\1[/pb_glossary]',l)
      term_fixes[t] += n
      fixes_this_file += n
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
    total_fixes += fixes_this_file
    files_with_fixes += 1
    new_fh.seek(0)
    new_fh.write(new_contents)
    new_fh.truncate()
    new_fh.close()
if total_fixes:
  log_and_print(f'Activated {total_fixes} glossary terms in {files_with_fixes} files (out of {len(files2fix)} files examined)')
  for t in terms:
    log_and_print(f'"{t}" activated {term_fixes[t]} times')
  update_fh.close()
else:
  log_and_print("No glossary terms needed activation!")
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
