#!/usr/bin/python

"""
ToDo: make it as a tcp server on port 40000, so that we can gracefully 'kill' it
"""
from PyQt4 import Qt, QtCore, QtNetwork
import sys
import argparse
import time
import os
import struct

USE_PYTHON_TIMER = True
LOCAL_TCP_PORT = 40000

DEF_SPINN_IP = '192.168.240.1'
SPINN_CHIP_X = 0
SPINN_CHIP_Y = 0
SPINN_PORT = 17893


PROFILER_CORE_ID = 1

SDP_SEND_RESULT_TAG = 1
DEF_HOST_SDP_PORT = 7        # port-7 has a special purpose, usually related with ETH

DEF_REPORT_TAG = 3
DEF_REPORT_PORT	= 40003
DEF_ERR_INFO_TAG = 4
DEF_ERR_INFO_PORT = 40004

HOST_REQ_PLL_INFO = 1
HOST_REQ_INIT_PLL = 2        # host request special PLL configuration
HOST_REQ_REVERT_PLL = 3
HOST_SET_FREQ_VALUE = 4        # Note: HOST_SET_FREQ_VALUE assumes that CPUs use PLL1,
                                            # if this is not the case, then use HOST_SET_CHANGE_PLL
HOST_REQ_PROFILER_STREAM = 5        # host send this to a particular profiler to start streaming
HOST_SET_GOV_MODE = 6
HOST_REQ_GOV_STATUS = 7
HOST_TELL_STOP = 255

#Governor mode:
GOV_USER = 0
GOV_ONDEMAND = 1
GOV_PERFORMANCE = 2
GOV_POWERSAVE = 3
GOV_CONSERVATIVE = 4
GOV_PMC = 5
GOV_QLEARNING = 6

DEF_USER_FREQ = 200

DELAY_IS_ON = True
DELAY_SEC = 0.01


class cGovController(QtCore.QObject):
    def __init__(self, govMode, freq, ip, parent=None):
        super(cGovController, self).__init__(parent)

        self.ip = ip
        self.govMode = govMode
        self.freq = freq

    # We can use sendSDP to control frequency, getting virtual core map, etc
    def sendSDP(self,flags, tag, dp, dc, dax, day, cmd, seq, arg1, arg2, arg3, bArray):
        """
        The detail experiment with sendSDP() see mySDPinger.py
        """
        da = (dax << 8) + day
        dpc = (dp << 5) + dc
        sa = 0
        spc = 255
        pad = struct.pack('2B',0,0)
        hdr = struct.pack('4B2H',flags,tag,dpc,spc,da,sa)
        scp = struct.pack('2H3I',cmd,seq,arg1,arg2,arg3)
        if bArray is not None:
            sdp = pad + hdr + scp + bArray
        else:
            sdp = pad + hdr + scp

        CmdSock = QtNetwork.QUdpSocket()
        CmdSock.writeDatagram(sdp, QtNetwork.QHostAddress(self.ip), SPINN_PORT)
        return sdp

    def start(self):
        dp = DEF_HOST_SDP_PORT
        dc = PROFILER_CORE_ID
        dax = SPINN_CHIP_X
        day = SPINN_CHIP_Y
        cmd = HOST_SET_GOV_MODE
        seq = self.govMode
        arg1 = self.freq
        print "[INFO] Sending HOST_SET_GOV_MODE"
        self.sendSDP(7,0,dp,dc,dax,day,cmd,seq,arg1,0,0,None)

        # then wait few seconds to check if it is applied
        time.sleep(2)
        cmd = HOST_REQ_GOV_STATUS
        print "[INFO] Sending HOST_REQ_GOV_STATUS"
        self.sendSDP(7,0,dp,dc,dax,day,cmd,seq,arg1,0,0,None)
        
        time.sleep(1)
        sys.exit(0)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Request specific governor to run.')
    parser.add_argument("-m", "--govMode", type=int, help="governor mode")
    parser.add_argument("-f", "--freq", type=int, help="required frequency in User Mode")
    parser.add_argument("-i", "--ip", type=str, help="SpiNNaker machine IP address")
    parser.add_argument("-s", "--showOnly", help="Show available governor and exit", action="store_true")
    args = parser.parse_args()
    if args.freq is None:
        args.freq = DEF_USER_FREQ
    if args.ip is None:
        args.ip = DEF_SPINN_IP

    if args.showOnly:
        print "Available governors:"
        print "--------------------"
        print "0 - User defined, the frequency must be supplied or use default {}-MHz".format(DEF_USER_FREQ)
        print "1 - On Demand"
        print "2 - Performance"
        print "3 - Powesave"
        print "4 - Conservative"
        print "5 - PMC-based"
        print "6 - Q-Learning-based"
        sys.exit(0)

    if args.govMode is None:
        print "Please specify the governor"
        sys.exit(-1)

    app = Qt.QCoreApplication(sys.argv)
    ctrl = cGovController(args.govMode, args.freq, args.ip, app)
    ctrl.start()
    sys.exit(app.exec_())

