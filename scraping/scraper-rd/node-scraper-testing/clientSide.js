// This is the code I made to get the data in the browser, can be converted to scrappy when ready.

// When looking for articles with a business id on http://www.rrk.ir/News/NewsList.aspx

// Send info to our server

function sendInfo(text) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", "http://localhost:3000/found");
    xhr.onload = function (event) {
        console.log("The server responded with: " + event.target.response);
    };
    xhr.send(text);
}

function getNextBusinessID(nextThing){
    let xhr = new XMLHttpRequest();
    xhr.open("GET", "http://localhost:3000/next");
    xhr.onload = function (event) {
        console.log("The server responded with: " + event.target.response);
        let j = JSON.parse(event.target.response);
        nextThing(j.cur);
    };
    xhr.send();
}


// Scrape info
// Send to server
// getBusinessID
// Fill and Click button!

function getPageInfo(){
    let businessID = document.body.querySelector("#cphMain_txtCompanySabtNumber").value;

    // true or false
    let noArticles = document.querySelector("#pnlSearchResults").innerHTML.search(/هیچ آگهیی پیدا نشد./g) != -1;
    
    let articleIds = document.querySelector("#pnlSearchResults").innerHTML.match(/(?!=ShowNews.aspx?Code=)\d{7}\d*(?=">)/g);

    let findings;
    if (noArticles && articleIds == null){
        findings = `${businessID}\t${articleIds}`
    } else {
        findings = `${businessID}\t${articleIds.join("\t")}`
    }
    console.log(findings);
    return findings;
}

function fillPageAndClick(id){
    document.body.querySelector("#cphMain_txtCompanySabtNumber").value = id;
    document.body.querySelector("#cphMain_btnSearch").click();
}


function main(){
    if (document.body.innerText.indexOf("Error reading from remote server") > -1 ||
        document.body.innerText.indexOf("Additionally, a 403 Forbidden error") > -1){
        location.reload();
    } else {
        if (document.querySelector("#pnlSearchResults")){
            sendInfo(getPageInfo());
        }
        getNextBusinessID(fillPageAndClick);
    }
}
main();