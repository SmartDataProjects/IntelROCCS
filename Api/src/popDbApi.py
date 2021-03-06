#!/usr/local/bin/python
#---------------------------------------------------------------------------------------------------
# Python interface to access Popularity Database. See website for API documentation
# (https://cms-popularity.cern.ch/popdb/popularity/apidoc)
#
# Use SSO cookie to avoid password
# (http://linux.web.cern.ch/linux/docs/cernssocookie.shtml)
# It is up to the caller to make sure a valid SSO cookie is obtained before any calls are made. A
# SSO cookie is valid for 24h. Requires usercert.pem and userkey.pem in ~/.globus/
#
# The API doesn't check to make sure correct values are passed or that rquired parameters are
# passed. All such checks needs to be done by the caller. All data is returned as JSON.
#
# In case of error an error message is printed to the log, currently specified by environemental
# variable INTELROCCS_LOG, and '0' is returned. User will have to check that something is returned.
# If a valid call is made but no data was found a JSON structure is still returned, it is up to
# the caller to check for actual data.
#---------------------------------------------------------------------------------------------------
import os, json, urllib, urllib2, datetime, subprocess, ConfigParser
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formataddr
from subprocess import Popen, PIPE

class popDbApi():
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'api.cfg'))
        self.fromEmail = config.items('from_email')[0]
        self.toEmails = config.items('error_emails')
        self.popDbBase = config.get('pop_db', 'base')
        self.cert = config.get('pop_db', 'certificate')
        self.key = config.get('pop_db', 'key')
        self.cookie = config.get('pop_db', 'sso_cookie')
        self.renewSsoCookie()

#===================================================================================================
#  H E L P E R S
#===================================================================================================
    def renewSsoCookie(self):
        # Will try to generate cookie 3 times before reporting an error
        for attempt in range(3):
            process = subprocess.Popen(["cern-get-sso-cookie", "--cert", self.cert, "--key", self.key, "-u", self.popDbBase, "-o", self.cookie], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
            process.communicate()[0]
            if process.returncode != 0:
                continue
            else:
                break
        else:
            self.error("Could not generate SSO cookie")
        return 0

    def call(self, url, values):
        data = urllib.urlencode(values)
        request = urllib2.Request(url, data)
        fullUrl = request.get_full_url() + request.get_data()
        strout = ""
        for attempt in range(3):
            process = subprocess.Popen(["curl", "-k", "-s", "-L", "--cookie", self.cookie, "--cookie-jar", self.cookie, fullUrl], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
            strout = process.communicate()[0]
            if process.returncode != 0:
                continue
            else:
                try:
                    jsonData = json.loads(strout)
                except ValueError:
                    continue
                break
        else:
            self.error("Pop DB call failed for url: %s %s" % (str(url), str(values)))
        return jsonData

    def error(self, e):
        title = "FATAL IntelROCCS Error -- Pop DB"
        text = "FATAL -- %s" % (str(e))
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = formataddr(self.fromEmail)
        msg['To'] = self._toStr(self.toEmails)
        msg1 = MIMEMultipart("alternative")
        msgText1 = MIMEText("<pre>%s</pre>" % text, "html")
        msgText2 = MIMEText(text)
        msg1.attach(msgText2)
        msg1.attach(msgText1)
        msg.attach(msg1)
        msg = msg.as_string()
        p = Popen(["/usr/sbin/sendmail", "-toi"], stdin=PIPE)
        p.communicate(msg)
        raise Exception("FATAL -- %s" % (str(e)))

    def _toStr(self, toEmails):
        names = [formataddr(email) for email in toEmails]
        return ', '.join(names)

#===================================================================================================
#  A P I   C A L L S
#===================================================================================================
    def DataTierStatInTimeWindow(self, tstart='', tstop='', sitename='summary'):
        values = {'tstart':tstart, 'tstop':tstop, 'sitename':sitename}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("DataTierStatInTimeWindow/"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR -- DataTierStatInTimeWindow call failed for values: tstart=%s, tstop=%s, sitename=%s\n" % (tstart, tstop, sitename))
        return jsonData

    def DSNameStatInTimeWindow(self, tstart='', tstop='', sitename='summary'):
        values = {'tstart':tstart, 'tstop':tstop, 'sitename':sitename}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("DSNameStatInTimeWindow/"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR -- DSNameStatInTimeWindow call failed for values: tstart=%s, tstop=%s, sitename=%s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tstart, tstop, sitename))
        return jsonData

    def DSStatInTimeWindow(self, tstart='', tstop='', sitename='summary'):
        values = {'tstart':tstart, 'tstop':tstop, 'sitename':sitename}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("DSStatInTimeWindow/"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR -- DSStatInTimeWindow call failed for values: tstart=%s, tstop=%s, sitename=%s\n" % (tstart, tstop, sitename))
        return jsonData

    def getCorruptedFiles(self, sitename='summary', orderby=''):
        values = {'sitename':sitename, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getCorruptedFiles/"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR -- getCorruptedFiles call failed for values: sitename=%s, orderby=%s\n" % (sitename, orderby))
        return jsonData

    def getDSdata(self, tstart='', tstop='', sitename='summary', aggr='', n='', orderby=''):
        values = {'tstart':tstart, 'tstop':tstop, 'sitename':sitename, 'aggr':aggr, 'n':n, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getDSdata"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR -- getDSdata call failed for values: tstart=%s, tstop=%s, sitename=%s, aggr=%s, n=%s, orderby=%s\n" % (tstart, tstop, sitename, aggr, n, orderby))
        return jsonData

    def getDSNdata(self, tstart='', tstop='', sitename='summary', aggr='', n='', orderby=''):
        values = {'tstart':tstart, 'tstop':tstop, 'sitename':sitename, 'aggr':aggr, 'n':n, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getDSNdata"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR -- getDSNdata call failed for values: tstart=%s, tstop=%s, sitename=%s, aggr=%s, n=%s, orderby=%s\n" % (tstart, tstop, sitename, aggr, n, orderby))
        return jsonData

    def getDTdata(self, tstart='', tstop='', sitename='summary', aggr='', n='', orderby=''):
        values = {'tstart':tstart, 'tstop':tstop, 'sitename':sitename, 'aggr':aggr, 'n':n, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getDTdata"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR: getDTdata call failed for values: tstart=%s, tstop=%s, sitename=%s, aggr=%s, n=%s, orderby=%s\n" % (tstart, tstop, sitename, aggr, n, orderby))
        return jsonData

    def getSingleDNstat(self, name='', sitename='summary', aggr='', orderby=''):
        values = {'name':name, 'sitename':sitename, 'aggr':aggr, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getSingleDNstat"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR: getSingleDNstat call failed for values: sitename=%s, aggr=%s, orderby=%s\n" % (sitename, aggr, orderby))
        return jsonData

    def getSingleDSstat(self, name='', sitename='summary', aggr='', orderby=''):
        values = {'name':name, 'sitename':sitename, 'aggr':aggr, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getSingleDSstat"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR: getSingleDSstat call failed for values: name=%s, sitename=%s, aggr=%s, orderby=%s\n" % (name, sitename, aggr, orderby))
        return jsonData

    def getSingleDTstat(self, name='', sitename='summary', aggr='', orderby=''):
        values = {'name':name, 'sitename':sitename, 'aggr':aggr, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getSingleDTstat"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR: getSingleDTstat call failed for values: name=%s, sitename=%s, aggr=%s, orderby=%s\n" % (name, sitename, aggr, orderby))
        return jsonData

    def getUserStat(self, tstart='', tstop='', collname='', orderby=''):
        values = {'tstart':tstart, 'tstop':tstop, 'collname':collname, 'orderby':orderby}
        url = urllib.basejoin(self.popDbBase, "%s?&" % ("getUserStat/"))
        jsonData = self.call(url, values)
        if not jsonData:
            self.error("ERROR: getUserStat call failed for values: tstart=%s, tstop=%s, collname=%s, orderby=%s\n" % (tstart, tstop, collname, orderby))
        return jsonData
