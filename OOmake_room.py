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
parser = argparse.ArgumentParser(description='Processes the HTML files from an OO PB to move them all one or more steps higher in numbering of sectins, so section X.Y will become X.(Y+s), where the shift s defaults to 1; also creates new manifest file in output directory')
parser.add_argument("manifest", help="File containing manifest of files to process; may contain CSS, FM, and/or BM lines, which will simply be skipped", type=argparse.FileType('r'))
parser.add_argument('-s', '--shift', help="amount to increase section numbers; default is 1 ", default=1)
parser.add_argument("-o", "--output", help="Name to use as output directory. If absent, will be shiftedOOhtml", default="shiftedOOhtml")
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "make_room.log".', default="make_room.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
args = parser.parse_args()
output = args.output
verbose = args.verbose
shift = args.shift
args.logfile.write("------------------------------------\n")
def log_and_print(s):
  t=time.strftime('%H:%M:%S')+" "+s
  args.logfile.write(t+"\n")
  if verbose:
    print(t)
log_and_print("On "+time.strftime('%d/%m/%Y')+", doing ")
log_and_print(' '.join(sys.argv)+" in directory "+os.getcwd())
os.mkdir(output)
log_and_print(f'Made directory {output}')
output += "/"
new_manifest_fh = open(output+"manifest","w")
mline_no = 0
def readml():
  global mline_no
  while True:
    mline_no += 1
    r = args.manifest.readline().strip()
    if not r or r[0]!="#":
      return(r)
mline = readml()
parens_contents = re.compile(r'[^(]*\(([^)]*)\).*')
bracket_contents = re.compile(r'[^[]*\[([1-9][0-9]*)\].*')
if mline[:5]=="CSS: ":
  new_manifest_fh.write(mline+"\n")
  mline = readml()
while mline[:4]=='FM: ' or mline[:4]=='BM: ' or mline[:6]=='Part: ':
  new_manifest_fh.write(mline+"\n")
  corresp_filename = readml()
  if not corresp_filename:
    raise ValueError("Malformed manfiest file on line {mline_no}: no filename after {mline}")
  new_manifest_fh.write(corresp_filename+"\n")
  mline = readml()
while mline[:8]=='Chapter[':
  old_chapter_filename = readml()
  if not old_chapter_filename:
    raise ValueError("Malformed manfiest file: no chapter filename on line {mline_no} after {mline}")
  chapter_ml_part_s = bracket_contents.sub(r'\1',mline)
  mline_prefix = mline[:mline.index(" ")+1]
  old_chapter_long_name = mline[mline.index(" ")+1:]
  old_chapter_short_name = old_chapter_long_name[old_chapter_long_name.index(" ")+1:]
  chapter_name_part_s = old_chapter_long_name[:old_chapter_long_name.index(".")]
  if chapter_ml_part_s != chapter_name_part_s:
    raise ValueError("Malformed manfiest file: section name's implied part number doesn't match what manifest says it should be on {mline_no}")
  old_chapter_sec_s = old_chapter_long_name[old_chapter_long_name.index(".")+1:old_chapter_long_name.index(" ")]
  old_XdotY = chapter_ml_part_s+"."+old_chapter_sec_s
  old_chapter_sec = int(old_chapter_sec_s)
  new_chapter_sec = old_chapter_sec + shift
  new_chapter_sec_s = str(new_chapter_sec)
  new_XdotY = chapter_ml_part_s+"."+new_chapter_sec_s
  new_manifest_fh.write(mline_prefix+new_XdotY+" "+old_chapter_short_name+"\n")
  new_chapter_filename = new_XdotY+".html"
  log_and_print(f"processing Chapter '{old_chapter_long_name}' in Part #{chapter_ml_part_s} from file '{old_chapter_filename}':")
  old_chapter_fh = open(old_chapter_filename, "r")
  new_chapter_full_fn = output+new_chapter_filename
  new_chapter_fh = open(new_chapter_full_fn, "w")
  new_manifest_fh.write(new_chapter_full_fn+"\n")
  old_XdotYpat = re.compile(r'(<h[1-6]( class="textbox__title")?>)'+old_XdotY)
  for old_chapter_line in old_chapter_fh:
    new_chapter_fh.write(old_XdotYpat.sub(r'\g<1>'+new_XdotY,old_chapter_line))
    if old_XdotYpat.search(old_chapter_line):
      log_and_print("changing: "+old_chapter_line+"\nto:       "+old_XdotYpat.sub(r'\g<1>'+new_XdotY,old_chapter_line))
    elif old_chapter_line.find(old_XdotY)>-1:
      print("found other old X.Y match on line: "+old_chapter_line)
  old_chapter_fh.close()
  new_chapter_fh.close()
  log_and_print(f"finished with {old_chapter_filename} -> {new_chapter_filename}")
  mline = readml()
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
args.logfile.write("------------------------------------\n")
args.logfile.close()
args.manifest.close()
new_manifest_fh.close()
