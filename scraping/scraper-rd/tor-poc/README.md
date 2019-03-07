# Tor Proofs of Concept

## Using the `IsolateSOCKSAuth` feature

`./tor_circuit_count_test.py` shows what happens when you use new SOCKS5 auth every so often to rotate identities (change exit nodes, flush DNS cache, etc.).

It turns out that circuits get reused somewhat often, and old circuits stick around for a while.
The former is inevitable because of the limited number of exit nodes, and the latter isn't really a problem because the main circuit overhead happens during creation.

The only interesting finding is that using new SOCKS5 auth doesn't always result in a new exit IP address, though cases where it doesn't change are uncommon.
The manual only says that SOCK5 clients using different auth will not share circuits, so I guess it's just a concidence that the new circuit uses the same exit node.
I don't see this as a real problem.

Getting old circuits to get garbage collected more often could probably be accomplished with a combination of `KeepAliveIsolateSOCKSAuth` and `MaxCircuitDirtiness=0`, and could definitely be accomplished with a `stem` script. However, as mentioned before, the keeping a circuit alive is cheap. However, it may or may not have an effect (in either direction) on circuit re-use for different socks auths, which we don't want. More experiments would be necessary.

## Tor with a `stem` script for rotating identities

This repository contains a proof of concept demonstrating the viability of one particular way of using Tor to mask and rotate IP addresses during scraping.

This approach uses one instance of Tor, listening on a control port, and listening on multiple Socks5 ports.
Each Socks5 port corresponds to one "identity" (one path through the Tor network and out of an exit node).
A client connecting to the internet using one Socks5 port will pop out at a different exit node (with a different IP address) than a client connecting using another Socks5 port.
The Tor control protocol allows us to ask Tor to change the identites of all Socks5 ports at once.

Suppose we want to pretend that n users are using the target website, each from a unique IP address, and that every t seconds those n users stop using the website, and n new users start, from all new IP addresses.
We would want these users to start their sessions at random delays after each t seconds, and to browse the website at a human speed.
So, to go faster, we would just increase n.

To achieve this effect, Tor could be configured to expose n Socks5 ports.
Every t seconds, Tor is instructed, through the control port, to rotate identites.

`start_tor.sh` and `tor_poc.py` prove that this would work.

This script could also be used to find Tor's limits (the upper limit on n) within whatever infrastructure we choose.
I've had no problems with n=20 and t=10.

#### Usage

```
./start_tor.sh CONTROL_PORT SOCKS_PORT_0 NUM_SOCKS_PORTS

python3 tor_poc.py CONTROL_PORT SOCKS_PORT_0 NUM_SOCKS_PORTS MIN_TIME_WITH_NYM

CONTROL_PORT:      Port for Tor to open to communicate with Tor controller (e.g. 9050)

SOCKS_PORT_0:      First Socks5 port to open (e.g. 9060)

NUM_SOCKS_PORTS:   Number of Socks5 ports to open, consecutively starting with
                   SOCKS_PORT_0. Corresponds to n in the example above.

MIN_TIME_WITH_NYM: Minimum time between identity rotations. Sometimes identities
                   can't rotate exactly when we ask them to. Corresponds to t in
                   the example above.
```

Tor will show some log output, and `tor_poc.py` will show the n clients and their external IP addresses as they change, which they fetch from `ipecho.nickspinale.com`.

Snapshot of example output of `tor_poc.py`:
```
identity changes: 2
now:              20.6213

socks port | last updated | ip addres or exception
-----------+--------------+-----------------------
      9060 |    20.613014 | 46.165.230.5
      9061 |    20.577819 | 185.220.102.7
      9062 |    20.207027 | 176.10.104.243
      9063 |    20.491904 | 204.85.191.30
      9064 |    20.356156 | 185.62.57.229
      9065 |    20.354260 | 185.104.120.60
      9066 |    19.641931 | 185.220.102.6
      9067 |    20.460896 | 185.220.101.20
      9068 |    19.859651 | 216.218.222.12
      9069 |    20.295474 | 204.8.156.142
      9070 |    20.388772 | 185.83.215.28
      9071 |    15.141364 | 37.187.129.166
      9072 |    20.063280 | 64.113.32.29
      9073 |    20.254496 | 95.168.216.16
      9074 |    20.392301 | 65.19.167.131
      9075 |    20.486249 | 62.102.148.67
      9076 |    20.463752 | 51.15.86.162
      9077 |    20.487544 | 185.62.57.229
      9078 |    19.902430 | 193.169.145.66
      9079 |    20.578314 | 64.27.17.140

log
---
     20.0970: newnym available
     20.0979: requested newnym
     20.0980: must wait 10.0 sec for newnym
```

#### Example

In one terminal:
```
./start_tor.sh 9050 9060 5
```
In another terminal:
```
python3 tor_poc.py 9050 9060 5 13
```

#### Dependencies

[Tor](https://www.torproject.org/).
You'll need the program `tor` in your path.
On Linux, installing Tor should be enough.
If you're on MacOS, try adding an executable file called `tor` somewhere in your path with the following:
```sh
#!/bin/sh
exec /Applications/TorBrowser.app/Contents/MacOS/Tor/tor.real "$@"
```

Python 3 with packages [requests](http://docs.python-requests.org/en/master/) and [stem](https://stem.torproject.org/), tested with the following versions:
```
requests==2.18.4
stem==1.6.0
```
