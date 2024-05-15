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
from bs4 import BeautifulSoup
import os
import re
import sys
import time
import code
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
parser = argparse.ArgumentParser(description='Finds the links from an html file such as the "tidy_book.html" produced by OOprep.py, putting links plus preceding and following context into an HTML file')
parser.add_argument("inputfile", help="File containing html from which to extract outline information.")
parser.add_argument("-l", "--logfile", help='Filename for logfile to which will be appended detailed progress information; default is "link_finder.log".', default="link_finder.log", type=argparse.FileType('a'))
parser.add_argument('-v', '--verbose', help="print on console all information also going in to the logfile", action='store_true')
parser.add_argument("-o", "--output", help='Name to use as base of output file (before the ".html"). If absent, will be "links_from_" prepended to input file name (after any ".html", if present, is removed).', default="")
parser.add_argument('-n', '--numbered_chapters', help='chapters have numbers, which are used in building the outline numbering', action='store_true')
parser.add_argument('-c', '--context', help='in the HTML file with all figures, include a paragraph before and after the figure, to ', action='store_true')
args = parser.parse_args()
verbose = args.verbose
inputfile = args.inputfile
in_fh = open(inputfile,'r')
if inputfile[-5:]==".html":
  infi_base=inputfile[:-5]
else:
  infi_base=inputfile
output = args.output
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
if output:
  out_fn_base = output
else:
  [dir,fn] = os.path.split(infi_base)
  if dir:
    dir += "/"
  out_fn_base = dir+'links_from_'+fn
html_out = open(out_fn_base+".html","w")
html_out.write(
f'''<!DOCTYPE html>
<html>
<head>
<meta content="text/html; charset=utf-8" http-equiv="content-type">
<title>Links</title>
</head>
<body>
<h1>Links</h1>
<hr style="width:100%">
''')
whole_book = in_fh.read()
book_lines = whole_book.split("\n")
locations = []
chap_no = 0
sec_no = 0
ssec_no = 0
sssec_no = 0
ssssec_no = 0
nesting_warnings = 0
this_location = ""
lines2print=[]
links=0
link_lines=0
html_lines=0
def warn(s):
  log_and_print(f'WARNING: on line {line_no}, with content\n{l}\n{s}')
for line_no in range(len(book_lines)):
  l = book_lines[line_no]
  if l[:4]=="<h1>":
    lines2print.append(line_no)
    html_out.write(l+"\n")
    if l[-5:]!="</h1>":
      warn("expecting entire line bracketed in <h1>..</h1>")
    if args.numbered_chapters:
      num = l.split()[1]
      if num[-1] == ":":
        num = num[:-1]
      chap_no = int(num)
    else:
      chap_no += 1
    sec_no = 0
    ssec_no = 0
    sssec_no = 0
    ssssec_no = 0
    this_location=f"Chapter {chap_no}"
    locations.append(this_location)
    log_and_print(f"found location {this_location}")
    continue
  if l[:4]=="<h2>":
    lines2print.append(line_no)
    html_out.write(l+"\n")
    if l[-5:]!="</h2>":
      warn("expecting entire line bracketed in <h2>..</h2>")
    if chap_no == 0:
      nesting_warnings += 1
      warn("Section without enclosing chapter")
    sec_no += 1
    ssec_no = 0
    sssec_no = 0
    ssssec_no = 0
    this_location = f"{chap_no}.{sec_no}"
    locations.append(this_location)
    log_and_print(f"found location {this_location}")
    continue
  if l[:4]=="<h3>":
    lines2print.append(line_no)
    html_out.write(l+"\n")
    if l[-5:]!="</h3>":
      warn("expecting entire line bracketed in <h3>..</h3>")
    if sec_no == 0:
      nesting_warnings += 1
      if chap_no == 0:
        warn("Subsection without enclosing chapter or section")
      else:
        warn("Subsection without enclosing section")
    ssec_no += 1
    sssec_no = 0
    ssssec_no = 0
    this_location = f"{chap_no}.{sec_no}.{ssec_no}"
    locations.append(this_location)
    log_and_print(f"found location {this_location}")
    continue
  if l[:4]=="<h4>":
    lines2print.append(line_no)
    html_out.write(l+"\n")
    if l[-5:]!="</h4>":
      warn("expecting entire line bracketed in <h4>..</h4>")
    if ssec_no ==0:
      nesting_warnings += 1
      if sec_no == 0:
        if chap_no == 0:
          warn("Subsubsection without enclosing chapter, section, or subsection")
        else:
          warn("Subsubsection without enclosing section or subsection")
      else:
        warn("Subsubsection without enclosing subsection")
    sssec_no += 1
    ssssec_no = 0
    this_location = f"{chap_no}.{sec_no}.{ssec_no}.{sssec_no}"
    locations.append(this_location)
    log_and_print(f"found location {this_location}")
    continue
  if l[:4]=="<h5>":
    lines2print.append(line_no)
    html_out.write(l+"\n")
    if l[-5:]!="</h5>":
      warn("expecting entire line bracketed in <h5>..</h5>")
    if sssec_no == 0:
      nesting_warnings += 1
      if ssec_no == 0:
        if sec_no == 0:
          if chap_no == 0:
            warn("Subsubsubsection without enclosing chapter, section, subsection, or subsubsection")
          else:
            warn("Subsubsubsection without enclosing section, subsection, or subsubsection")
        else:
          warn("Subsubsubsection without enclosing subsection or subsubsection")
      else:
        warn("Subsubsubsection without enclosing subsubsection")
    ssssec_no += 1
    this_location = f"{chap_no}.{sec_no}.{ssec_no}.{sssec_no}.{ssssec_no}"
    locations.append(this_location)
    log_and_print(f"found location {this_location}")
    continue
  locations.append(this_location)
  soup=BeautifulSoup(l)
  soup_a_list = soup.find_all("a")
  if soup_a_list:
    links += len(soup_a_list)
    link_lines += 1
    last_line_no = line_no-1
    if args.context:
      if not last_line_no in lines2print:
        if book_lines[last_line_no] == "</table>":
          table_start=line_no-2
          lines2print.append(table_start)
          while book_lines[table_start][:6] != "<table":
            table_start -= 1
            lines2print.append(table_start)
            if not table_start:
              raise ValueError(f"table near line {line_no} seems to have no start!")
          html_out.write('<table border="1px"\n')
          html_out.writelines(tablin+"\n" for tablin in book_lines[table_start+1:line_no])
        elif book_lines[last_line_no] == "</ol>":
          list_start=line_no-2
          lines2print.append(list_start)
          while book_lines[list_start][:3] != "<ol":
            list_start -= 1
            lines2print.append(list_start)
            if not list_start:
              raise ValueError(f"ordered list near line {line_no} seems to have no start!")
          html_out.writelines(listlin+"\n" for listlin in book_lines[list_start:line_no])
        elif book_lines[last_line_no] == "</ul>":
          list_start=line_no-2
          lines2print.append(list_start)
          while book_lines[list_start] != "<ul>":
            list_start -= 1
            lines2print.append(list_start)
            if not list_start:
              raise ValueError(f"ordered list near line {line_no} seems to have no start!")
          html_out.writelines(listlin+"\n" for listlin in book_lines[list_start:line_no])
        lines2print.append(last_line_no)
        html_out.write(book_lines[last_line_no]+"\n")
      if l[:4] == "<li>":
        # go back and forward to get the entire list
        0
      elif book_lines[last_line_no] == "<td>":
        # go back and forward to get the entire table
        table_start=line_no-2
      else:
        lines2print.append(line_no)
        html_out.write(l+"\n")
        next_line_no = line_no-1
        if book_lines[next_line_no][:6] == "<table":
          table_end=next_line_no+1
          lines2print.append(table_end)
          while book_lines[table_end] != "</table>":
            table_end += 1
            lines2print.append(table_end)
            inner_soup = BeautifulSoup(book_lines[table_end])
            inner_soup_a_list = inner_soup.find_all("a")
            if inner_soup_a_list:
              links += len(inner_soup_a_list)
              link_lines += 1
            if table_end>len(book_lines):
              raise ValueError(f"table near line {line_no} seems to have no end!")
          html_out.write('<table border="1px"\n')
          html_out.writelines(tablin+"\n" for tablin in book_lines[next_line_no+1:table_end+1])
        elif book_lines[next_line_no][:3] == "<ol":
          list_end=next_line_no+1
          lines2print.append(list_end)
          while book_lines[list_end] != "</ol>":
            list_end += 1
            lines2print.append(list_end)
            inner_soup = BeautifulSoup(book_lines[list_end])
            inner_soup_a_list = inner_soup.find_all("a")
            if inner_soup_a_list:
              links += len(inner_soup_a_list)
              link_lines += 1
            if list_end>len(book_lines):
              raise ValueError(f"ordered list near line {line_no} seems to have no end!")
          html_out.writelines(listlin+"\n" for listlin in book_lines[next_line_no:list_end+1])
        elif book_lines[next_line_no] == "<ul>":
          list_end=next_line_no+1
          lines2print.append(list_end)
          while book_lines[list_end] != "</ul>":
            list_end += 1
            lines2print.append(list_end)
            inner_soup = BeautifulSoup(book_lines[list_end])
            inner_soup_a_list = inner_soup.find_all("a")
            if inner_soup_a_list:
              links += len(inner_soup_a_list)
              link_lines += 1
            if list_end>len(book_lines):
              raise ValueError(f"ordered list near line {line_no} seems to have no end!")
          html_out.writelines(listlin+"\n" for listlin in book_lines[next_line_no:list_end+1])
        lines2print.append(last_line_no)
        html_out.write(book_lines[last_line_no]+"\n")
    else:
      lines2print.append(line_no)
      html_out.write(l+"\n")
if nesting_warnings:
  if nesting_warnings >1:
    log_and_print(f"Exiting: there were {nesting_warnings} improperly nested section warnings")
  if nesting_warnings == 1:
    log_and_print(f"Exiting: there was an improperly nested section warning")
  quit()
html_out.write('<hr style="width:100%">\n<p>&nbsp;</p>\n')
html_out.write('<p>Please note that the material on this page <b>is not by Jonathan Poritz</b> but is instead by various Open Oregon Educational Resources authors, and those authors (or their employers) are the rightsholders and have chosen the copyright status of their work.  Excerpts are posted here with the permission of Open Oregon Educaitonal Resources and are only for OOER internal use.</p>\n')
html_out.write(f"<p>{when_work} at {time.strftime('%H:%M:%S')} did {what_work}</p>\n")
html_out.write(f"<p>processed {len(book_lines)} lines of HTML</p>\n")
html_out.write(f"<p>found {links} links on {link_lines} lines</p>\n")
html_out.write(f"<p>wrote {len(set(lines2print))} lines of HTML output (not including header and footer)</p>\n")
html_out.write("</body>\n</html>\n")
html_out.close()
log_and_print(f"processed {len(book_lines)} lines of HTML")
log_and_print(f"found {links} links on {link_lines} lines")
log_and_print(f"wrote {len(set(lines2print))} lines of HTML output (not including header and footer)")
#code.interact(local=locals())
