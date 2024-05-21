# GoDot2PB Workflow

## Ensure python is installed

Copy the following line and paste into your command line terminal to check if python is already installed

    python --version

If not, navigate to https://www.python.org/downloads/ to download the latest version

### Set pip system path

To check if the system path was added, run the following command

    echo %PATH%

Look for a path similar to C:\Users\<YourUsername>\AppData\Local\Programs\Python\PythonXX\Scripts\

If the path is not included, follow these remaining steps:

1. Run “start %APPDATA%” in the terminal
3. A folder should open called "Roaming." Click the up arrow to go to the parent folder called AppData.
4. Go to Local, then Programs, then Python, then Python###, then Scripts
5. Copy this path
6. In the taskbar search menu, search for "View Advanced System Settings"
7. Click "Environment Variables" in the bottom right
8. In the upper box, click on "Path" so that it is highlighted blue
9. Click the edit button beneath the upper window, click new, and paste in the path copied earlier
10. Click "Ok" on all 3 windows to exit out of the environment variables tab
11. Close and reopen your terminal

### Install packages

Next, ensure all supporting packages are installed successfully (full list can be found at https://poritz.net/jonathan/share/GoDot2P/)
* all packages should be included by default, except a few. To add these, run the following in your terminal
*     pip install beautifulsoup4
      pip install requests
      pip install selenium

## Download the repo as a ZIP

Click the green "<> Code" dropdown to download the code as a ZIP. Unzip the folder in your location of choice

* To install tidy, navigate to https://binaries.html-tidy.org/ and download the recent version for your operating system. Make sure to install the package in the same directory as the code files from this repository. If you're using windows, download the .msi version to automatically set Path variables
* To install pandoc, navigate to https://github.com/jgm/pandoc/releases/tag/3.2 and download the recent version for your operating system. Make sure to install the package in the same directory as the code files from this repository. If you're using windows, download the .msi version to automatically set Path variables

## Export your Google Doc

Download your Google Doc as a web page (File -> Download -> Webpage)

Unzip the folder into the same directory with the files from this repository

Rename the resulting .html file to book.html

## Prepare your Pressbooks Chapter

In your command line terminal, copy and paste the following code to navigate to the directory holding the code
* tip: click on the top bar of your file explorer to copy the file path of your directory
*     cd replace/me/with/path/to/directory/

Run the following commands in the terminal 

    python OOprep -v -b "cX cY" book.html
    python OOoutliner -n -t tidy_book.html

If OOoutliner gave you warnings, that means there are structural issues with your headers in the html. Fix the warnings and try again!

### Images

If your Google Doc has images, run this command as well
    
    python OOimg_list -v -o imgs tidy_book.html
    
Open your book in Pressbooks, and click on the "Import" tab. Import imgs.docx into pressbooks 

### Text
Copy the contents of the tidy_book.html file and paste into the Pressbooks text editor 

# Acknowledgements

Copyright (C) 2023 Jonathan A. Poritz
 
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See more here: https://poritz.net/jonathan/share/GoDot2P/
