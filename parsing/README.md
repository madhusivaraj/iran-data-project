# Iran Parsing

## Running the Script
* Make sure you have python3 install and `pip` install `bs4` and `jdatetime`
* Next mount or clone the s3 bucket (to mount use s3fs and after setting up your
  credentials run `s3fs -o
  allow_other,uid=1000,gid=1000,umask=227,use_cache=/tmp/cache iran-article-html
  s3mnt/`
* Note: the scraped articles are now at `s3mnt/` (if the records are in a different directory
  replace all references of s3mnt in the following steps with that name.
* Clone the full repo in the same directory `s3mnt/` is located.
* Now run `python3 iran-data-project/parsing/threaded_parser.py s3mnt >>
  log.txt`. Open `log.txt` to see how the parse is doing.
* Once it's complete (full parse will take more than a day), sync to Mongo by
  executing from the same directory as above `python3
  iran-data-project/parsing/mongo_sync.py records/`
* You are good to go!

## Overview
* Beautiful Soup can extract the text contents.
* Regex can then be used to extract the names and dates based upon patterns
  we've discovered in the text.

## Parsing Details
* Company National ID - This first checks the section of the document that is
  somewhat of a title and where the national ID is usually located. If none is
  found, it then checks the body of the document for any national ID and returns
  one if present.
* Various Dates - Dates are very orderd and the document dates are actually
  stored in their own divs with html ids we can just pull. The rest of the dates
  can be pulled by finding their general location and relation and then pulling
  every date using regex and grabbing them in a sensical order. If this isn't
  100% correct, it likely won't block general use of the dates for reporting.
* [Deprecated] Names (Regex) - The regex uses identified patterns for the various name locations to
  pull the name area. This might accidently miss part of a name or include
  additional name parts not actually needed, but currently is very accurate for
  most documents.
* Names (Name Sandwhich) - This uses a list of words that always precede a name
  and a list of words that always proceed a name. It then finds everything
  instance in the document in which a word in the preceding list is followed by
  a word in the proceeding list within 40 characters. All of these occurences
  are then added as names and if a 10 digit number appears within 40 characters
  of the preceding value its added as the ID (if multiple it picks the first one
  found)
* Names (Double Tap) - This identifies every 10 digit number in the text and
  then looks for signs around it that would imply its a name. Such signs
  include Mr., Mrs., etc. It then saves the chunk that is likely a name.
* [Deprecated] Names (Entity Recognition) - This method finds proper nouns and matches them
  to the various places in a the text names are mentioned.

## Example Documents
* [http://www.rrk.ir/News/ShowNews.aspx?Code=13343917](http://www.rrk.ir/News/ShowNews.aspx?Code=13343917)
