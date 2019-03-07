const fs = require('fs');
var stream = fs.createWriteStream("append.txt", {flags:'a'});


var express = require('express');
var app = express();
var bodyParser = require('body-parser');
app.use(bodyParser.text());
// Add headers
app.use(function (req, res, next) {

    // Website you wish to allow to connect
    res.setHeader('Access-Control-Allow-Origin', '*');

    // Request methods you wish to allow
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');

    // Request headers you wish to allow
    res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');

    // Set to true if you need the website to include cookies in the requests sent
    // to the API (e.g. in case you use sessions)
    res.setHeader('Access-Control-Allow-Credentials', true);

    // Pass to next layer of middleware
    next();
});


// respond with "hello world" when a GET request is made to the homepage
app.get('/', function (req, res) {
  res.send('hello world')
})

app.get('/next', function (req, res) {
    let rand = Math.floor(Math.random()*lines.length);
    let next = lines[rand];
    lines.splice(rand, 1);
    if (next == undefined) throw ("Next is undefined. Check depend.txt")
    console.log("we got " + next);
    let obj = {cur : next}
    res.send(JSON.stringify(obj));
    deleteLine(rand);
})

app.post('/found', function(req,res){
    writeToFile(req.body);
    console.log(new Date().toTimeString() + "\t" + req.body);
    res.send("done")
});

app.listen(3000, () => console.log('Example app listening on port 3000!'))


function writeToFile(txt){
    stream.write(txt + "\n");
}


function deleteLine(lineNumber){
    let filename = "depend.txt";
    fs.readFile(filename, 'utf8', function (err, data) {
        if (err) console.log(err);
        let lines = data.split('\n');
        let removed = lines.splice(lineNumber, 1).join('\n');
        console.log("removed " + removed);
        //fs.writeFile(filename, data, function () { });
    });
}


// This automatically loads the businessIds in memory
let lines;
let lineCounter = 0;
getLines();
function getLines(){
    let filename = "depend.txt";
    fs.readFile(filename, 'utf8', function (err, data) {
        if (err) {
            console.log(err);
        }
        lines = data.split('\n');
        console.log("Lines loaded");
    });
}