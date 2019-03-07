# captcha-storage

## Overview

We experimented with creating a Json Store of solved captchas in a different server than the scraper with a technology called
Firebase. This is useful if there are multiple scrapers; we are able to share solutions to captcha's across all scrapers.
In practice, it didn't work very well because oftentimes the correct solution to a captcha was rejected by the website we crawled as incorrect.

### Deploy

1. Create a [FireBase](https://firebase.google.com/) and create a new project. Copy the credentials into the config file in this repo.
2. Create an account on [Heroku](https://www.heroku.com/platform)
3. Deploy this service on your heroku account
4. Follow usage instructions below

# Usage

Send a `GET` request to:

`https://captcha-storage.herokuapp.com/captcha/oso3iNjM4ckMu2kUeJRhnQ==`

A JSON object with the structure as stated above will be returned.

To update the database send a `POST` request to: 

`https://captcha-storage.herokuapp.com/captcha/oso3iNjM4ckMu2kUeJRhnQ==`

In the body send the updated JSON in the body and it will be updated for everyone.

## Properties

* key - The unique code that is associated with each captcha.
* base64encoding - A string representation of the image. Should be sent with any unsolved captcha so we can view it later.
* solution - the answer to the captcha.
* failed-attempts - solutions we tried in the past so you don't have to waste a post request.

The API by sends and receives objects with the following structure.
```
{
    "key": "oso3iNjM4ckMu2kUeJRhnQ==",
    "base64encoding": "",
    "solution": 151,
    "failed-attempts": [150, 167]
}
```
