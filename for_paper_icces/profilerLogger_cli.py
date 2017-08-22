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


#/*--- For JPEG file ---*/
SDP_PORT_JPEG_DATA = 1
SDP_PORT_JPEG_INFO     = 2
#/*--- For Raw RGB file ---*/
SDP_PORT_RAW_DATA    = 3
SDP_PORT_RAW_INFO   = 4
#/*--- For both ---*/
SDP_CMD_INIT_SIZE    = 1
SDP_CMD_CLOSE_IMAGE    = 2
SDP_CMD_REPORT_TMEAS  =  3

SDP_RECV_CORE_ID = 2    

SDP_SEND_RESULT_TAG = 1
SDP_SEND_RESULT_PORT = 30000
DEF_HOST_SDP_PORT = 7        # port-7 has a special purpose, usually related with ETH

HOST_REQ_PLL_INFO = 1
HOST_REQ_INIT_PLL = 2        # host request special PLL configuration
HOST_REQ_REVERT_PLL = 3
HOST_SET_FREQ_VALUE = 4        # Note: HOST_SET_FREQ_VALUE assumes that CPUs use PLL1,
                                            # if this is not the case, then use HOST_SET_CHANGE_PLL
HOST_REQ_PROFILER_STREAM = 5        # host send this to a particular profiler to start streaming
HOST_SEQ_GOV_MODE = 6
HOST_TELL_STOP = 255


DELAY_IS_ON = True
DELAY_SEC = 0.01


class cLogger(QtCore.QObject):
    def __init__(self, logName=None, parent=None):
        super(cLogger, self).__init__(parent)
        #QtGui.QWidget.__init__(self, parent)
        self.ip = DEF_SPINN_IP
        self.logName = logName

        """
        The format of profiler data:
        ushort v;           # profiler version, in cmd_rc
        ushort pID;         # which chip sends this?, in seq
        uchar cpu_freq;     # in arg1
        uchar rtr_freq;     # in arg1
        uchar ahb_freq;     # in arg1
        uchar nActive;      # in arg1
        ushort  temp1;         # from sensor-1, for arg2
        ushort temp3;         # from sensor-3, for arg2
        uint memfree;       # optional, sdram free (in bytes), in arg3
        uchar load[18];
        """

        self.setupTCP() #for acting as a server that can be killed gracefully
        self.setupUDP() #for retrieving data from SpiNNaker

        self.isRunning = False

    def setupUDP(self):
        self.sdpRecv = QtNetwork.QUdpSocket(self)
        print "[INFO] Trying to open UDP port-{}...".format(SDP_SEND_RESULT_PORT),
        ok = self.sdpRecv.bind(SDP_SEND_RESULT_PORT)
        if ok:
            print "done!"
            self.sdpRecv.readyRead.connect(self.readSDP)
            self.fmt = '<2H4B2HI18B'
            self.szData = struct.calcsize(self.fmt)
            print "[INFO] Require {}-byte data".format(self.szData)
            self.isUdpReady = True
        else:
            print "fail!"
            self.isUdpReady = False

    def setupTCP(self):
        self.tcp = QtNetwork.QTcpServer(self)
        if self.tcp.listen(QtNetwork.QHostAddress.LocalHost, LOCAL_TCP_PORT) is False:
            print "[WARNING] Cannot open port-{}".format(LOCAL_TCP_PORT)
        else:
            self.tcp.newConnection.connect(self.killMe)

    @QtCore.pyqtSlot()
    def killMe(self):
        self.isRunning = False

    @QtCore.pyqtSlot()
    def readSDP(self):
        while self.sdpRecv.hasPendingDatagrams():
            sz = self.sdpRecv.pendingDatagramSize()
            # NOTE: readDatagram() will produce str, not bytearray
            datagram, host, port = self.sdpRecv.readDatagram(sz)
            ba = bytearray(datagram)

        # don't continue recording if 'killing' signal is received
        if self.isRunning is False:
            return

        # remove the first 10 bytes of SDP header
        del ba[0:10]
        if len(ba) == self.szData:
            c = [0 for _ in range(18)]
            v, pID, fCPU, fRTR, fAHB, nActive, temp1, temp3, mem, c[0], c[1], c[2], c[3], c[4],
            c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12], c[13], c[14], c[15], c[16],
            c[17] = struct.unpack(self.fmt, ba)
        
            s = '%d,%d,%d,%d,%d,%d,%d,%d,%d'%(v,pID,fCPU,fRTR,fAHB,nActive,temp1,temp3,mem)
            for i in range(18):
                s += ',%d'%c[i]

            s += '{}'.format(time.time())

            self.logFile.write(s)

    def prepareLogFile(self):
        #prepare to save data
        if self.logName is None:
            LOG_DIR = "./experiments/"
            cmd = "mkdir -p {}".format(LOG_DIR)
            os.system(cmd)
            self.fname = LOG_DIR + 'profiler_' + time.strftime("%b_%d_%Y-%H.%M.%S", time.gmtime()) + ".log"
        else:
            if self.logName.find(".log") == -1:
                self.logName += ".log"
            self.fname = self.logName
        print "[INFO] Preparing log-file: {}".format(self.fname)
        self.logFile = open(self.fname, "w")

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

    def setSpiNNconnection(self, req):
        if req is True:
            print "[INFO] Connecting to SpiNNaker..."
            #send streaming request...
            dp = DEF_HOST_SDP_PORT
            cmd = HOST_REQ_PROFILER_STREAM
            seq = 1
            self.sendSDP(7,0,dp,1,SPINN_CHIP_X,SPINN_CHIP_Y,cmd,seq,0,0,0,None)
        else:
            print "[INFO] Disconnecting from SpiNNaker..."
            #send streaming request...
            dp = DEF_HOST_SDP_PORT
            cmd = HOST_REQ_PROFILER_STREAM
            seq = 0
            self.sendSDP(7,0,dp,1,SPINN_CHIP_X,SPINN_CHIP_Y,cmd,seq,0,0,0,None)

    def start(self):
        if self.isUdpReady is False:
            sys.exit(-1)
        self.prepareLogFile()
        #send request to start streaming
        self.setSpiNNconnection(True)

        self.isRunning = True # will be set False by 'killing' on port LOCAL_TCP_PORT

        while isRunning:
            try:
                QtCore.QCoreApplication.processEvents()
            except KeyboardInterrupt:
                break

        self.stop()

    def stop(self):
        #send request to stop streaming
        self.setSpiNNconnection(False)

        #and close the file
        self.logFile.close()
        print "[INFO] Recording is done!"
        sys.exit(0)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Power Data Logger')
    parser.add_argument("-l", "--logname", type=str, help="Log filename")
    args = parser.parse_args()

    app = Qt.QCoreApplication(sys.argv)
    logger = cLogger(args.logname, app)
    logger.start()
    sys.exit(app.exec_())

