# Node-scraper-testing

The purpose of this was to setup a very rudimentary test to see if scraping the AritcleIDs given BusinessIDs was feasible.

**tl;dr it's not really worth the time.**


## Findings
The server takes a very long time to respond (from a 30 seconds to 5 minutes) if there are any articles linked to the `businessID` and concurrent queries don't help. Also since we already have a small sample data [here](https://github.com/nspin/iran-data-project/blob/master/node-scraper-testing/append.txt) we can see that most articleIDs are in a smilar area. 

## How it works

index.js runs locally creating a small webserver. The webserver reads business IDs from `depend.txt` and then deletes them after being used. It sends lines to `append.txt` in the format of `businessID \t articleIDs`.

Once the server is running you can just run `clientSide.js` in your browser on the website http://www.rrk.ir/News/newsList.aspx and it'll get a businessID, search it, and send the articleIDs.


## Recommended Next Steps
I think that we should avoid this step of scraping these `articleIDs` and start scraping the articles by incrementing the counter. The start number can be determined from the current `articleIDs` in `append.txt`.