# GoDot2PB Workflow

## Ensure python is installed

Copy the following line and paste into your command line terminal to check if python is already installed

    python --version

If not, navigate to https://www.python.org/downloads/ to download the latest version

Next, ensure all supporting packages are installed successfully (full list can be found at https://poritz.net/jonathan/share/GoDot2P/)
* all packages should be included by default, except beautifulsoup4, requests, and selenium. to add these, run the following in your terminal
*     pip install beautifulsoup4
      pip install requests
      pip install selenium


## Download the repo as a ZIP

Click the green "<> Code" dropdown to download the code as a ZIP. Unzip the folder in your location of choice

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

### Images

If your Google Doc has images, run this command as well
    
    python OOimg_list -v -o imgs tidy_book.html
    
Open your book in Pressbooks, and click on the "Import" tab. Import imgs.docx into pressbooks 

### Text
Copy the contents of the tidy_book.html file and paste into the Pressbooks text editor 
