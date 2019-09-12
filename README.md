# ActiveReign

<p align="center">
  <img src="https://user-images.githubusercontent.com/13889819/62736481-6f7e7880-b9fb-11e9-92d6-47b650fdb84b.png"/>
  <br>
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg"/>&nbsp;
  <img src="https://img.shields.io/badge/License-GPLv3-green.svg">&nbsp;
  <!--<img src="https://img.shields.io/badge/Demo-Youtube-red.svg"/>&nbsp;-->
  <a href="https://twitter.com/intent/follow?screen_name=m8r0wn">
     <img src="https://img.shields.io/twitter/follow/m8r0wn?style=social&logo=twitter" alt="follow on Twitter"></a>
</p>

### Background
A while back I was challenged to write a discovery tool with Python3 that could automate the process of finding sensitive information on network file shares. After writing the entire tool with pysmb, and adding features such as the ability to open and scan docx an xlsx files, I slowly started adding functionality from the awesome [Impacket](https://github.com/SecureAuthCorp/impacket) library; just simple features I wanted to see in an internal penetration testing tool. The more I added, the more it looked like a Python3 rewrite of [CrackMapExec](https://github.com/byt3bl33d3r/CrackMapExec) created from scratch. 
 
If you are doing a direct comparison, [CME](https://github.com/byt3bl33d3r/CrackMapExec) is an amazing tool that has way more features than currently implement here. However, I added a few modifications that may come in handy during an assessment.

### For more documentation checkout the project [wiki](https://github.com/m8r0wn/ActiveReign/wiki)

### Operational Modes
* db    - Query or insert values in to the ActiveReign database
* enum  - System enumeration & module execution
* shell - Spawn an emulated shell on a target system
* spray - Domain password spraying and brute force
* query - Perform LDAP queries on the domain


### Key Features
* Automatically extract domain information via LDAP and incorporate into network enumeration.
* Perform Domain password spraying using LDAP to remove users close to lockout thresholds.
* Local and remote command execution, for use on multiple starting points throughout the network.
* Emulated interactive shell on target system
* Data discovery capable of scanning xlsx and docx files.
* Various modules to add and extend capabilities.


### Acknowledgments
There were many intended and unintended contributors that made this project possible. If I am missing any, I apologize, it was in no way intentional. Feel free to contact me and we can make sure they get the credit they deserve ASAP!
* [@byt3bl33d3r](https://github.com/byt3bl33d3r) -  [CrackMapExec](https://github.com/byt3bl33d3r/CrackMapExec)
* [@SecureAuthCorp](https://github.com/SecureAuthCorp) - [Impacket](https://github.com/SecureAuthCorp/impacket)
* [@the-useless-one](https://github.com/the-useless-one) - [pywerview](https://github.com/the-useless-one/pywerview)
* [@dirkjanm](https://github.com/dirkjanm) - [ldapdomaindump](https://github.com/dirkjanm/ldapdomaindump)

### Final Thoughts

Writing this tool and testing on a variety of networks/systems has taught me that execution method matters, and depends on the configuration of the system. If a specific module or feature does not work, determine if it is actually the program, target system, configuration, or even network placement before creating an issue.

To help this investigation process, I have created a ```test_execution``` module to run against a system with known admin privileges. This will cycle through all all execution methods and provide a status report to determine the best method to use:
```bash
$ activereign enum -u administrator -p password -d demo.local -M test_execution dc02.demo.local
[*] Lockout Tracker             Using default lockout threshold: 3
[*] Enum Authentication         demo.local\administrator (Password: p****) (Hash: False)
[+] DC02.demo.local             192.168.1.28    ENUM             Windows Server 2012 R2 Standard Evaluation 9600 x64(Domain: DEMO)   (Signing: True)  (SMBv1: True) (Adm!n) 
[*] DC02.demo.local             192.168.1.28    TEST_EXECUTION   Testing execution methods...                   
[*] DC02.demo.local             192.168.1.28    TEST_EXECUTION   Execution Method: WMIEXEC    Fileless: SUCCESS   Remote (Defualt): SUCCESS
[*] DC02.demo.local             192.168.1.28    TEST_EXECUTION   Execution Method: SMBEXEC    Fileless: SUCCESS   Remote (Defualt): SUCCESS
```
