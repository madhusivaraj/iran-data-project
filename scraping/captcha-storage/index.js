var express = require('express')
var app = express()
app.use(express.json());
app.listen(process.env.PORT || 3000)


app.get('/', function (req, res) {
  res.send('Hello World')
})

app.get('/captcha/:id', function (req, res, next) {
    console.log('Sending info for ' + req.params.id);
    firebase.database().ref('/captcha/' + req.params.id).once('value')
    .then(function(snapshot) {
        let val = snapshot.val();
        if (val == null){
            let temp = {
                "key": req.params.id,
                "base64encoding": "",
                "solution": "",
                "failed-attempts": [""]
            }
            writeCaptcha(req.params.id, temp);
            val = temp;
        }
        res.send(val);
      })
      .catch(e => {
          console.log(e);
      })
});

// Sends all the current captcha info known
app.get('/captchas', function (req, res, next) {
    console.log('Sending info for ' + req.params.id);
    firebase.database().ref('/captcha/').once('value')
    .then(function(snapshot) {
        let val = snapshot.val();
        res.send(val);
      })
      .catch(e => {
          console.log(e);
      })
});


app.post('/captcha/:id', function (req, res, next) {
    console.log('Accepting post for ' + req.params.id);
    console.log(req.body);
    writeCaptcha(req.params.id, req.body)
    res.send({
        "status": "recieved"
    });
});


// Initialize Firebase
let firebase = require("firebase");
let config = process.env.firebase ? JSON.parse(process.env.firebase) : require("./config.json").firebase;
firebase.initializeApp(config);

function writeCaptcha(captchaid, json) {
    firebase.database().ref('captcha/' + captchaid).update(json);
}
