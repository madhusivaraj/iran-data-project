# Python Scraper

This directory contains a scraper written in Python.

### Result:

We crawled documents with url `/News/ShowNews.aspx?Code=x` where the code parameter was between 12,000,000-14,000,000. 
We didn't want to crawl in sequential order since adversaries could predict the order of our crawl. In order to introduce
an amount of pseudo-randomness, we used the formuala

`code to crawl = 12,000,000 + ((32,452,867 * index) % 2,000,001))`

where `32,452,867` is a prime number. It is important the prime number is larger than the range and `%` is the modulus operator. 
For more details about this approach, see `iran-data-project/scraper/py-scraper/scraper/document_store/code_tracker.py`

We crawled all urls of the form `/News/ShowNews.aspx?Code=x` where `index` is in one of the ranges below.

* 0 - 382,788
* 600,000 - 717517
* 850,000 - 967,630 
* 1,100,000 -  1,297,530
* 1,350,000 - 1,498,000
* 1,500,000- 2,000,000 

Adding up the total number of positions in the above ranges, we get 1,463,465 URLs crawled. Note that this includes URLs
that don't have an article associated with them.

### Run Locally

`./tests/test_local.py` contains a working demonstration which uses local storage backends.

### Using Docker

1. `cd` into the py-scraper directory, build the image.

`docker build -t <name-of-image> .`

2. Run the image as a container, providing AWS and DataDog secrets as environment variables and possibly command line arguments to `scripts/main.py`.

`docker run --name <name-of-container> [-d, to run in background] -v <log volume name>:/logs:rw --env-file scraper_secrets.env <name-of-image> [arguments to scripts/main.py, such as --start-index 3 --nthreads 15]`

where `scraper_secrets.env` might contain:

```
DATADOG_API_KEY=these
DATADOG_APP_KEY=are
AWS_ACCESS_KEY=super
AWS_SECRET_KEY=secret
```

If you don't want `scripts/start.sh` to run immediately, use this instead:

`docker run --name <name-of-container> --env-file scraper_secrets.env --entrypoint /bin/sh -it <name-of-image>`

#### Deployment

There is a local Docker registry on our ec2 instance on localhost:5000.
With an ssh port forward localhost:5000->localhost:5000, deployment should be a simple as:

```
# on local machine
docker build -t localhost:5000/scraper .
docker push localhost:5000/scraper

# on ec2 instance
docker pull localhost:5000/scraper
docker run ... localhost:5000/scraper ...
```

This means that each time you make a small change to the image, you only send new layers over the network, instead of an entire debian distribution or whateover the network, instead of an entire debian distribution or whatever.

However, this isn't working, and I haven't been able to figure out the problem, despite the fact that I can access the registry via curl on my local machine (through an ssh port forward, of course).

So, for now, this will have to do:

```
# on local machine
docker build -t scraper .
docker save scraper | ssh -C ...@... docker load
docker run ... scraper ...
```

#### Tips

Bash into container:

`docker exec -i -t <name-of-container> /bin/bash`

Stop all docker containers:

`docker kill $(docker ps -q)`

Remove all stopped docker containers:

`docker rm $(docker ps -q)`

Read docker logs:

`docker logs <container-name>`

Copy docker file to host directory:

`docker cp <containerId>:/file/path/within/container /host/path/target`

### Dependencies

- python 3.6.5
- modules in requirements.txt
- tesseract binary
    - `brew install tesseract` for mac
    - `sudo apt-get tesseract-ocr` for ubuntu
    
### S3 setup

The two buckets we are using for this project are `iran-article-html` and `iran-article-html-test`

### Storage Backends

`scraper.captcha_cache.LocalCaptchaCache` and `scraper.document_store.LocalDocumentStore` use local SQLite databases and directories.

`scraper.aptcha_cache.RemoteCaptchaCache` uses the REST API found in `../captcha-storage`.

`scraper.document_store.RemoteDocumentStore` will use a remote SQL database and S3 buckets, or just S3 buckets with some hacks to store metadata about documents.
For example, what we ultimately want is a mapping from article codes in a range to whether the document is present, absent, or redirects to a ShowOldNews URL, and, if it's present, the document itself.
Having a SQL database storing the metadata (present, absent, or old) and a flat S3 bucket just storing article that were present by their codes might be the simplest solution.
