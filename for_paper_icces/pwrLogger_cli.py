#!/usr/bin/python

#This is the cli version of pwrLogger. Intended for
#scripting (no gui).

from PyQt4 import Qt, QtCore, QtNetwork
import sys
import argparse
import time
import os
import struct

USE_PYTHON_TIMER = True

LOCAL_TCP_PORT = 40001


class cLogger(QtCore.QObject):
    def __init__(self, ip, port, mode, logName=None, parent=None):
        super(cLogger, self).__init__(parent)
        #QtGui.QWidget.__init__(self, parent)
        self.ip = ip
        self.port = int(port)
        self.mode = int(mode)
        self.logName = logName
        self.blockSize = 0
        if self.mode==2:
            self.fmt = '<i'
        else:
            self.fmt = '<10i'
        self.szData = struct.calcsize(self.fmt)
        print "[INFO] Require {}-byte data for mode-{}".format(self.szData, self.mode)
        self.setupTCP()
        self.isStarted = False

    def setupTCP(self):
        self.tcp = QtNetwork.QTcpSocket(self)
        if self.mode<2:
            self.tcp.readyRead.connect(self.readData0)
        else:
            self.tcp.readyRead.connect(self.readData2)
        self.tcp.error.connect(self.tcpError)

        # and for the killer
        self.killer = QtNetwork.QTcpServer(self)
        if self.killer.listen(QtNetwork.QHostAddress.LocalHost, LOCAL_TCP_PORT) is False:
            print "[WARNING] Cannot open port-{}".format(LOCAL_TCP_PORT)
        else:
            print "[INFO] my closing port is {}".format(LOCAL_TCP_PORT)
            self.killer.newConnection.connect(self.killMe)

    def killMe(self):
        self.isRunning = False

    def start(self):
        self.isStarted = True

        #prepare to save data
        LOG_DIR = "./experiments/"
        cmd = "mkdir -p {}".format(LOG_DIR)
        os.system(cmd)
        if self.logName is None:
            self.fname = LOG_DIR + 'pwr_' + time.strftime("%b_%d_%Y-%H.%M.%S", time.gmtime()) + ".log"
        else:
            if self.logName.find(".log") == -1:
                self.logName += ".log"
            self.fname = LOG_DIR + self.logName
        print "[INFO] Preparing log-file: {}".format(self.fname)
        self.logFile = open(self.fname, "w")
        print "[INFO] Connecting to Raspberry Pi..."
        self.tcp.connectToHost(self.ip, self.port)
        self.isRunning = True
        while self.isRunning:
            try:
                QtCore.QCoreApplication.processEvents()
            except KeyboardInterrupt:
                break

        self.stop()

    def stop(self):
        self.isStarted = False
        self.tcp.disconnectFromHost()
        print "[INFO] Trying to disconnect from Raspberry Pi..."
        #close the file
        #self.logFile.flush()
        #os.fsync(self.logFile)
        self.logFile.close()
        print "[INFO] Recording is done!"
        #self.quit()
        #Qt.QCoreApplication.quit()
        sys.exit(0)

    @QtCore.pyqtSlot()
    def tcpError(self, socketError):
        if socketError == QtNetwork.QAbstractSocket.RemoteHostClosedError:
            pass
        elif socketError == QtNetwork.QAbstractSocket.HostNotFoundError:
            print "[ERROR] The host was not found. Please check the host name and port settings."
        elif socketError == QtNetwork.QAbstractSocket.ConnectionRefusedError:
            print "[ERROR] The connection was refused by the server. Make sure the server is running, and check that the host name and port settings are correct."
        else:
            print "[ERROR] The following error occurred: %s." % self.tcp.errorString()

    @QtCore.pyqtSlot()
    def readData0(self):
        if self.isRunning is False:
            return
        """
        # The following will produce TypeError: object of type 'NoneType' has no len()
        instr = QtCore.QDataStream(self.tcp)
        instr.setVersion(QtCore.QDataStream.Qt_4_0)

        if self.blockSize == 0:
            if self.tcp.bytesAvailable() < 2:
                return

            self.blockSize = instr.readUInt16()

        if self.tcp.bytesAvailable() < self.blockSize:
            return

        nextFortune = instr.readString()
        self.logFile.write(str(len(nextFortune)))
        """

        # since data arrives "asynchronousl", i.e. in multiple of 32-bytes
        # it is unwise to add timestamp in python, rather it should be
        # sent by raspi. However, the second portion can be generated here
        # only the usec portion will be sent by raspi.

        # read all as bytearray
        #print self.tcp.bytesAvailable()
        if self.tcp.bytesAvailable() < self.szData:
            return

        ba = self.tcp.read(self.szData)
        #print len(ba)

        #while self.tcp.bytesAvailable() >= self.szData:
        d1,d2,d3,d4,d5,d6,d7,d8,ts,tu = struct.unpack(self.fmt, ba)
        d = '{},{},{},{},{},{},{},{},{}.{}\n'.format(d1,d2,d3,d4,d5,d6,d7,d8,ts,tu)
        if USE_PYTHON_TIMER:
            ts = '%lf'%time.time()
            d = '{},{},{},{},{},{},{},{},{}\n'.format(d1,d2,d3,d4,d5,d6,d7,d8,ts)
        else:
            d = '{},{},{},{},{},{},{},{},{}.{}\n'.format(d1,d2,d3,d4,d5,d6,d7,d8,ts,tu)
        self.logFile.write(d)


    @QtCore.pyqtSlot()
    def readData2(self):
        """
        For continuous mode.
        """
        if self.isRunning is False:
            return

        # read all as bytearray
        while self.tcp.bytesAvailable() >= self.szData:
            ba = self.tcp.read(self.szData)
            d1 = struct.unpack(self.fmt, ba)
            dstr = str(d1[0])
            t = '%lf' % time.time()
            d = '{},{}\n'.format(dstr,t)
            self.logFile.write(d)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Power Data Logger')
    parser.add_argument("-i", "--ip", type=str, help="Raspberry Pi IP-address, usually 10.99.192.101")
    parser.add_argument("-p", "--port", type=str, help="Raspberry Pi port, usually 30001")
    parser.add_argument("-l", "--logname", type=str, help="Log filename")
    parser.add_argument("-m", "--mode", type=str, help="sampling mode (0=8-ch, 2=1-ch)")
    args = parser.parse_args()
    if args.ip is None or args.port is None or args.mode is None:
        print "Please provide the Raspberry Pi IP and port as well as sampling mode"
        sys.exit(-1)
    if int(args.mode) < 0 or int(args.mode) > 2:
        print "Invalid mode!"
        sys.exit(-1)

    app = Qt.QCoreApplication(sys.argv)
    logger = cLogger(args.ip, args.port, args.mode, args.logname, app)
    logger.start()
    sys.exit(app.exec_())
