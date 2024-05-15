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
import code
import sys
import time
import uuid
import warnings
import tempfile
from tidylib import tidy_document

if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Process a prepared html file in various ways to load into Pressbooks')
parser.add_argument("input_file", help="Source html file", type=argparse.FileType('rb'))
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "split.log".', default="split.log")
parser.add_argument('--lol', help="Learning Objectives sections consist entirely of an <ol>", action='store_true')
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument("-i", "--image_file", help="Html file from PB image upload pseudo-section; default is pb_imgs.html.", default="pb_imgs.html")
parser.add_argument("-m", "--manifest", help="Name to use as manifest file for later uploading with OOupload.py. If absent, will be 'manifest'", default="manifest")
parser.add_argument("-p", "--preamble", help="Name manifest preamble file. If absent, there will be no preamble", default="")
parser.add_argument("-o", "--output", help="Name to use as output directory. If absent, will be OOhtml", default="OOhtml")
parser.add_argument("-k","--key_terms_strong", help='manually makes the terms in the Key Terms section strong, i.e., any line of the form "<li><term>: <other text>" in the Key Terms section becomes "<li><strong><term></strong>: <other text>"; default is False', action='store_true')
parser.add_argument("-n","--numbered_sections", help='asserts that the sections and subsections at all levels have been pre-numbered -- however, they will be newly numbered and discrepancies will be reported; default is False', action='store_true')
args = parser.parse_args()
output = args.output
verbose = args.verbose
preamble = args.preamble
imgfile = args.image_file
strong_KTs = args.key_terms_strong
numbered_sects = args.numbered_sections
logfile_fh = open(args.logfile,"a")
logfile_fh.write("------------------------------------\n")
def log_and_print(s):
  t=time.strftime('%H:%M:%S')+" "+s
  logfile_fh.write(t+"\n")
  if verbose:
    print(t)
when_work = "On "+time.strftime('%d/%m/%Y')
log_and_print(when_work+", doing ")
what_work = ' '.join(sys.argv)+" in directory "+os.getcwd()
log_and_print(what_work)

#temp_fn="/tmp/"+str(uuid.uuid4())
#tidy_command = 'tidy -g -q -o '+temp_fn+' -w 0 '+imgfile+" 2> /dev/null"
#os.system(tidy_command)
#log_and_print(f'Did {tidy_command}')
#img_fh = open(temp_fn, 'r')
#img_file_s = img_fh.read()
#img_fh.close()
#os.system('del '+temp_fn)

temp_fn = tempfile.NamedTemporaryFile(delete=False).name
with open(temp_fn, 'w') as temp_fh:
    document, errors = tidy_document(open(imgfile, 'r').read())
    temp_fh.write(document)

log_and_print(f'Did tidy operation on {imgfile}')

with open(temp_fn, 'r') as img_fh:
    img_file_s = img_fh.read()

os.remove(temp_fn)

img_x=0
os.mkdir(output)
log_and_print(f'Made directory {output}')
h2pat = re.compile(r'<h2>([1-9]+[0-9]*)\.([0-9]*) (.*)</h2>\n') 
h3pat = re.compile(r'<h3>([1-9]+[0-9]*)\.([0-9]*)\.([0-9]*) (.*)</h3>\n') 
h4pat = re.compile(r'<h4>([1-9]+[0-9]*)\.([0-9]*)\.([0-9]*)\.([0-9]*) (.*)</h4>\n')
h5pat = re.compile(r'<h5>([1-9]+[0-9]*)\.([0-9]*)\.([0-9]*)\.([0-9]*)\.([0-9]*) (.*)</h5>\n')
preamble_lines = 0
manifest_chapter_lines = 0
manifest_part_lines = 0
manifest_fh = open(output+"/"+args.manifest,'w')
manifest_fh.write("# "+when_work+", this was\n")
manifest_fh.write("# "+what_work+" which resulted in this file\n")
if preamble:
  preamble_fh=open(preamble,'r')
  for line in preamble_fh:
    preamble_lines += 1
    manifest_fh.write(line)
  preamble_fh.close()
  if len(line) and line[-1]!="\n":
    manifest_fh.write("\n")
  log_and_print(f'Wrote {preamble_lines} manifest preamble lines')
current_filename=output+"/"+"1"+".0.html"
current_fh = open(current_filename,"w")
new_html_files = 0
total_html_lines = 0
KT_pattern=re.compile('<li>([^:]+):')
sect_title = ''
chap_no = ""
line_no = 0
manifest_chapters = ""
learn_obj_header = "<div class=\"textbox textbox--learning-objectives\"><header class=\"textbox__header\">\n<p class=\"textbox__title\">Learning Objectives</p>"
# current_fh.write('<div class="textbox textbox--examples"><header class="textbox__header">\n')
# current_fh.write('<h2>'+chap_no+"."+str(sect_no)+"."+str(sub_sect_no)+"."+str(sub_sub_sect_no)+" Going Deeper</h2>\n")
# current_fh.write('</header>\n')
# current_fh.write('<div class="textbox__content">\n')
# total_html_lines += 4

while True:
  line = args.input_file.readline().decode()
  if not line:
    break
  line_no += 1
  if "<h1" in line:
    close = args.input_file.readline().decode()
    close = args.input_file.readline().decode()
    if "</h1>" not in close:
      raise ValueError("malformed line with h1 tag: "+line+" on line "+str(line_no))
    current_fh.write("</div>\n")
    total_html_lines += 1
    if current_fh:
      current_fh.close()
    next_pos = args.input_file.tell()
    next_line = args.input_file.readline().decode()
    args.input_file.seek(next_pos)
    chap_no=next_line[next_line.find(">")+1:next_line.find("</")]
    sect_no=0
    sect_title = ''
    sub_sect_no=0
    sub_sub_sect_no=0
    sub_sub_sub_sect_no=0
    current_filename=output+"/"+chap_no+".0.html"
    current_fh = open(current_filename,"w")
    new_html_files += 1
    current_fh.write("Click on the <strong>+</strong> in the <strong>Contents</strong> menu to see all the parts of this chapter, or go through them in order by clicking <strong>Next →</strong> below.\n")
    total_html_lines += 1
    manifest_part_lines += 1
    manifest_fh.write("Part: "+line[4:-6]+"\n"+current_filename+"\n")
  elif line[:3] == "<h2":
    if line[-6:-1] != "</h2>":
      raise ValueError("malformed line with h2 tag: "+line+" on line "+str(line_no))
    sect_no += 1
    if numbered_sects:
      if not h2pat.match(line):
        raise ValueError("malformed line with h2 tag: "+line+" on line "+str(line_no))
      declared_chap_no = h2pat.sub(r'\1',line)
      declared_sect_no = int(h2pat.sub(r'\2',line))
      if (declared_chap_no != chap_no) or (declared_sect_no != sect_no):
        log_and_print(f'Level two heading "{line[4:-6]}" should be numbered {chap_no}.{str(sect_no)}; correcting!')
      sect_title = h2pat.sub(r'\3',line)
    else:
      sect_title = line[4:-6]
    sub_sect_no=0
    sub_sub_sect_no=0
    sub_sub_sub_sect_no=0
    if current_fh:
      current_fh.close()
    current_filename = output+"/"+chap_no+"."+str(sect_no)+".html"
    current_fh = open(current_filename,"w")
    new_html_files += 1
    manifest_chapter_lines += 1
    manifest_chapters += "Chapter["+chap_no+"]: "+chap_no+"."+str(sect_no)+" "+sect_title+"\n"+current_filename+"\n"
  elif line[:3] == "<h3":
    if line[-6:-1] != "</h3>":
      raise ValueError("malformed line with h3 tag: "+line+" on line "+str(line_no))
    sub_sect_no += 1
    if numbered_sects:
      if not h3pat.match(line):
        raise ValueError("malformed line with h3 tag: "+line+" on line "+str(line_no))
      declared_chap_no = h3pat.sub(r'\1',line) 
      declared_sect_no = int(h3pat.sub(r'\2',line))
      declared_sub_sect_no = int(h3pat.sub(r'\3',line))
      if (declared_chap_no != chap_no) or (declared_sect_no != sect_no) or (declared_sub_sect_no != sub_sect_no):
        log_and_print(f'Level three heading "{line[4:-6]}" should be numbered {chap_no}.{str(sect_no)}.{str(sub_sect_no)}; correcting!')
      ssect_title = h3pat.sub(r'\4',line)
    else:
      ssect_title = line[4:-6]
    sub_sub_sect_no=0
    sub_sub_sub_sect_no=0
  elif line[:3] == "<h5":
    if line[-6:-1] != "</h5>":
      raise ValueError("malformed line with h5 tag: "+line+" on line "+str(line_no))
    sub_sub_sub_sect_no += 1
    if numbered_sects:
      if not h5pat.match(line):
        raise ValueError("malformed line with h5 tag: "+line+" on line "+str(line_no))
      declared_chap_no = h5pat.sub(r'\1',line)
      declared_sect_no = int(h5pat.sub(r'\2',line))
      declared_sub_sect_no = int(h5pat.sub(r'\3',line))
      declared_sub_sub_sect_no = int(h5pat.sub(r'\4',line))
      declared_sub_sub_sub_sect_no = int(h5pat.sub(r'\5',line))
      if (declared_chap_no != chap_no) or (declared_sect_no != sect_no) or (declared_sub_sect_no != sub_sect_no) or (declared_sub_sub_sect_no != sub_sub_sect_no) or (declared_sub_sub_sub_sect_no != sub_sub_sub_sect_no):
        log_and_print(f'Level five heading "{line[4:-6]}" should be numbered {chap_no}.{str(sect_no)}.{str(sub_sect_no)}.{str(sub_sub_sect_no)}.{str(sub_sub_sub_sect_no)}; correcting!')
      ssssect_title = h5pat.sub(r'\6',line)
    else:
      sssssect_title = line[4:-6]
    current_fh.write("<h3>"+chap_no+"."+str(sect_no)+"."+str(sub_sect_no)+"."+str(sub_sub_sect_no)+"."+str(sub_sub_sub_sect_no)+" "+sssssect_title+"</h3>\n")
    total_html_lines += 1
  else:
# the stuff below doesn't handle nested tables very well...
    x=0
    while "<img" in line[x:]:
      y0=x+line[x:].find("<img")+4
      y=y0+line[y0:].find("src=")+5
      current_fh.write(line[x:y])
      if not "<img" in img_file_s[img_x:]:
        raise ValueError("not enough img tags in "+imgfile+" for line #"+str(line_no)+":\n"+line+"\nremainder of image file is:\n"+img_file_s[img_x:])
      img_y0=img_x+img_file_s[img_x:].find("<img")+4
      img_y=img_y0+img_file_s[img_y0:].find("src=")+5
      img_y1=img_y+img_file_s[img_y:].find('"')
      current_fh.write(img_file_s[img_y:img_y1])
      img_x=img_y1
      x=y+line[y:].find('"')
    current_fh.write(line[x:])
    total_html_lines += 1

if "<img" in img_file_s[img_x:]:
  raise ValueError(f"{img_file_s[img_x:].count('<img') } too many img tags in {imgfile}")
if current_fh:
  current_fh.close()
  new_html_files += 1
log_and_print(f'Wrote {manifest_part_lines} manifest part lines')
manifest_fh.write(manifest_chapters)
log_and_print(f'Wrote {manifest_chapter_lines} manifest chapter lines')
manifest_fh.close()
log_and_print(f'Created {new_html_files} new html files in {output}')
log_and_print("Done (on "+time.strftime('%d/%m/%Y')+")!")
logfile_fh.write("------------------------------------\n")
logfile_fh.close()