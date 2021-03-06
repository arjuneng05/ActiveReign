'''
 Help from:
https://github.com/the-useless-one/pywerview/blob/master/pywerview/requester.py
https://github.com/the-useless-one/pywerview/blob/master/pywerview/functions/net.py
'''

from impacket.dcerpc.v5.dcom import wmi
from impacket.dcerpc.v5.dtypes import NULL
from impacket.dcerpc.v5.dcomrt import DCOMConnection
from impacket.dcerpc.v5.dcom.wmi import WBEM_FLAG_FORWARD_ONLY

from ar3.logger import highlight
from ar3.core.connector import Connector

class WmiCon(Connector):
    def __init__(self, args, loggers, ip, host):
        Connector.__init__(self, args, loggers, ip)
        """Display var passed for output formatting but, IP is used to
           establish to connection, as hostname can be inconsistent"""
        self.display_ip   = ip
        self.display_host = host
        self._debug       = False
        self.dcom         = None
        self.wmi_con      = None
        self.process_list = {}

    def create_wmi_con(self, namespace='root\\cimv2'):
        self.dcom = DCOMConnection(self.host, self.username, self.password, self.domain, self.lmhash, self.nthash)
        iInterface = self.dcom.CoCreateInstanceEx(wmi.CLSID_WbemLevel1Login,wmi.IID_IWbemLevel1Login)
        iWbemLevel1Login = wmi.IWbemLevel1Login(iInterface)
        self.wmi_con = iWbemLevel1Login.NTLMLogin('\\\\{}\\{}'.format(self.host, namespace), NULL, NULL)

    def get_netprocess(self, tasklist=False):
        self.create_wmi_con()
        wmi_enum_process = self.wmi_con.ExecQuery('SELECT * from Win32_Process', lFlags=WBEM_FLAG_FORWARD_ONLY)
        while True:
            try:
                wmi_process = wmi_enum_process.Next(0xffffffff, 1)[0]
                wmi_process_owner = wmi_process.GetOwner()
                attributes = {'computername': self.host,
                              'processname': wmi_process.Name,
                              'processid': wmi_process.ProcessId,
                              'user': wmi_process_owner.User,
                              'domain': wmi_process_owner.Domain}
                # Dont wait until end to print
                if tasklist:
                    self.logger.info([self.display_host, self.display_ip, "TASKLIST","PID: {:<6} Name: {:<20} User: {:<17} Host: {:<15} Domain: {}".
                                format(attributes['processid'], attributes['processname'], attributes['user'],
                                       attributes['computername'], attributes['domain'])])
                self.process_list[wmi_process.ProcessId] = attributes

            except Exception as e:
                if str(e).find('S_FALSE') < 0:
                    self.logger.debug( "Get-NetProcess: {}".format(str(e)))
                else:
                    break
        self.disconnect()

    def wmi_query(self,namespace, query):
        self.create_wmi_con(namespace)
        wmi_query = self.wmi_con.ExecQuery(query, lFlags=WBEM_FLAG_FORWARD_ONLY)
        while True:
            try:
                wmi_results = wmi_query.Next(0xffffffff, 1)[0]
                wmi_results = wmi_results.getProperties()
                for k,v in wmi_results.items():
                    self.logger.info([self.display_host, self.display_ip, 'WMI QUERY', "{:<30} {}".format(k, v['value'])])

            except Exception as e:
                if str(e).find('S_FALSE') < 0:
                    self.logger.debug( "WMIQuery: {}".format(str(e)))
                else:
                    break
        self.disconnect()

    def disconnect(self):
        self.dcom.disconnect()