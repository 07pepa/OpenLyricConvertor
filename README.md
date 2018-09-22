# OpenLyricConvertor
Convertor of openlyric XML to *.usr supporded by pro presenter


With help of [openLP](https://openlp.org/) it can convert old pro presenter formats epicworship and other

you just need to import it to open lp (it must show all characters correctly in openlp) and export it out of it...


further conversion is done by convert.py

convert script need just newest [python 3](https://www.python.org/downloads/)
## speed of translation
Translation is speady ( on machine with i5-7200U with SSD translate about 100 files per second)
but on slower machines or machines without ssd  it can be slower.... please wait til end of translation.
proces of one file is singified with rotation of slash /  (one change =one file)

## Usage
you place convert.py into directory with your songs in openlyric format and run it(from same directory)
on windows there is conviniency runners (windows-run-Me...en/cz) on linux it is advised to cd into directory and run it

... script will tell you how many xml it founded and ask you to path to folder where to place result

path can be absolute (/home/someuser|c:/users/me/desktop/)
and relative ./ (curent folder)  ../ (parent folder)   ../folder_in_parent
path can (but does not have to ) have slash (/ or \) at end...

## Problems
There are some problems with this program 1st... if multiple files have same title then only 1st one file is translated and folowing are ignored (and reported on end of translation)
also if name contain slash (/ \) slash is changed to ／ 


oficialy windows and linux is supported
