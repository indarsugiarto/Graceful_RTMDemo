#!/usr/bin/python

# -------- SpiNNaker-related parameters --------

# NOTE: This must compatible with SpinJPEG.h

#-- port and cmd_rc
SDP_RECV_JPG_DATA_PORT = 1
SDP_RECV_JPG_INFO_PORT = 2
SDP_RECV_RAW_DATA_PORT = 3
SDP_RECV_RAW_INFO_PORT = 4
SDP_CMD_INIT_SIZE = 1
SDP_CMD_CLOSE_IMAGE = 2 #only for video processing, not image

# if aplx detect SDP_DATA_TYPE_IMAGE, it will close sdramImgBuf right after decoding it
# but if SDP_DATA_TYPE_VIDEO is received, it will not close sdramImgBuf until it
# receives SDP_CMD_CLOSE_IMAGE
SDP_DATA_TYPE_IMAGE = 1
SDP_DATA_TYPE_VIDEO = 2

SDP_SEND_RESULT_PORT = 30000
SDP_RECV_CORE_ID = 2
DEC_MASTER_CORE = SDP_RECV_CORE_ID
ENC_MASTER_CORE = 10
SPINN_HOST = '192.168.240.253'
SPINN_PORT = 17893
DEBUG_MODE = 0
DELAY_IS_ON = True
#DELAY_SEC = 0.1  # useful for debugging
DELAY_SEC = 0.0001  # for release mode

from PyQt4 import Qt, QtCore, QtGui, QtNetwork
import sys
import struct
import argparse
import time
import os
from spinConfig import *


class cEncoderTester(QtGui.QWidget):
    def __init__(self, imgFile, wImg, hImg, SpiNN, parent=None):
        super(cDecoderTester, self).__init__(parent)

        # prepare the sdp receiver
        self.setupUDP()

    def setupUDP(self):
        self.sdpRecv = QtNetwork.QUdpSocket(self)
        print "[INFO] Trying to open UDP port-{}...".format(SDP_SEND_RESULT_PORT),
        ok = self.sdpRecv.bind(SDP_SEND_RESULT_PORT)
        if ok:
            print "done!"
        else:
            print "fail!"
        self.sdpRecv.readyRead.connect(self.readSDP)

    def resetRecvBuf(self):
        self.resultImg = bytearray()

    def saveResult(self):
        # self.resultImg is a complete jpg image
        self.fResultName = str(self.fName).replace(".ra1",".jpg")
        print "[INFO] Writing result to:", self.fResultName
        with open(self.fResultName, "wb") as bf:
            bf.write(self.resultImg)


    @QtCore.pyqtSlot()
    def readSDP(self):
        while self.sdpRecv.hasPendingDatagrams():
            sz = self.sdpRecv.pendingDatagramSize()
            # NOTE: readDatagram() will produce str, not bytearray
            datagram, host, port = self.sdpRecv.readDatagram(sz)
            ba = bytearray(datagram)
            if DEBUG_MODE > 0:
                print "Got sdp length {}-bytes".format(sz)
        # remove the first 10 bytes of SDP header
        del ba[0:10]
        if len(ba) > 0:
            if DEBUG_MODE > 0:
                print "Append datagram length {}-bytes".format(len(ba))
            self.resultImg += ba
        else:
            if DEBUG_MODE > 0:
                print "Got EOF. Save to file!"
            self.saveResult()


    def setupGui(self):
        self.setWindowTitle("Tester")
        # add a button
        self.pbLoadSend = QtGui.QPushButton(self)
        self.pbLoadSend.setGeometry(QtCore.QRect(0, 0, 92, 29))
        self.pbLoadSend.setObjectName("pbLoadSend")
        self.pbLoadSend.setText("Load-n-Send")
        self.connect(self.pbLoadSend, QtCore.SIGNAL("clicked()"), QtCore.SLOT("pbLoadSendClicked()"))

    @QtCore.pyqtSlot()
    def pbLoadSendClicked(self):
        if self.loadImg() is True:
            self.resetRecvBuf()
            self.sendImg()

    def loadImg(self):
        self.fName = QtGui.QFileDialog.getOpenFileName(caption="Load Image File",
                                                       filter="Raw Gray Image (*.ra1)")
        if self.fName == "" or self.fName is None:
            print "[INFO] Ups... cancelled!"
            self.fName = None
            return False
        else:
            self.wImg, ok = QtGui.QInputDialog.getInt(self, "Get Image Width", "Width (px)")
            if ok is False:
                return False
            self.hImg, ok = QtGui.QInputDialog.getInt(self, "Get Image Height", "Height (px)")
            if ok is False:
                return False
            print "[INFO] Loading raw image: ", self.fName
            # read the raw data and put into memory
            # for info see this: http://www.devdungeon.com/content/working-binary-data-python
            with open(self.fName, "rb") as bf:
                self.orgImg = bf.read()     # read the whole file at once
            return True

    def sendImg(self):
        """
        Note: udp packet is composed of these segments:
              mac_hdr(14) + ip_hdr(20) + udp_hdr(8) + sdp + fcs(4)
              hence, udp_payload = 14+20+8+4 = 46 byte
        """
        print "[INFO] Sending image info to SpiNNaker...",
        self.sendImgInfo()
        print "done!"

        szImg = len(self.orgImg)    # length of original data
        print "[INFO] Start sending raw image data of {}-bytes to SpiNNaker...".format(szImg)
        #iterate until all data in self.orgImg is sent
        cntr = 0
        szSDP = 272                 # length of a chunk
        szRem = szImg               # size of remaining data to be sent
        sPtr = 0                    # start index of slicer
        ePtr = szSDP                # end index of slicer
        while szRem > 0:
            if szSDP < szRem:
                chunk = self.orgImg[sPtr:ePtr]
            else:
                szSDP = szRem
                chunk = self.orgImg[sPtr:]
            cntr += 1
            if DEBUG_MODE > 0:
                print "Sending chunk-{} with len={}-bytes out of {}-bytes".format(cntr, len(chunk)+8, szRem) 
            self.sendChunk(chunk)
            szRem -= szSDP
            sPtr = ePtr
            ePtr += szSDP
        # finally, send EOF (end of image transmission)
        if DEBUG_MODE > 0:
            print "Sending EOF (10-to) byte SpiNNaker..."
        self.sendChunk(None)
        print "[INFO] All done in {} chunks!".format(cntr)


    def sendImgInfo(self):
        dpc = (SDP_RECV_RAW_INFO_PORT << 5) + SDP_RECV_CORE_ID  # destination port and core
        pad = struct.pack('2B', 0, 0)
        hdr = struct.pack('4B2H', 7, 0, dpc, 255, 0, 0)
        scp = struct.pack('2H3I', SDP_CMD_INIT_SIZE, 0, len(self.orgImg), self.wImg, self.hImg)
        sdp = pad + hdr + scp
        CmdSock = QtNetwork.QUdpSocket()
        CmdSock.writeDatagram(sdp, QtNetwork.QHostAddress(self.spinn), SPINN_PORT)
        CmdSock.flush()
        # then give a break, otherwise spinnaker might collapse
        self.delay()

    def sendChunk(self, chunk):
        # based on sendSDP()
        # will be sent to chip <0,0>, no SCP
        dpc = (SDP_RECV_RAW_DATA_PORT << 5) + SDP_RECV_CORE_ID  # destination port and core
        pad = struct.pack('2B', 0, 0)
        hdr = struct.pack('4B2H', 7, 0, dpc, 255, 0, 0)
        if chunk is not None:
            sdp = pad + hdr + chunk
        else:
            # empty sdp means end of image transmission
            sdp = pad + hdr
        CmdSock = QtNetwork.QUdpSocket()
        CmdSock.writeDatagram(sdp, QtNetwork.QHostAddress(self.spinn), SPINN_PORT)
        CmdSock.flush()
        # then give a break, otherwise spinnaker will collapse
        self.delay()

    def delay(self):
        if DELAY_IS_ON:
            time.sleep(DELAY_SEC)


# ---------------------------- end of class cViewerDlg -----------------------------------


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Encoding JPG in SpiNNaker')
    parser.
    parser.add_argument("-ip", type=str, help="ip address of SpiNNaker")
    args = parser.parse_args()

    app = Qt.QApplication(sys.argv)
    gui = cViewerDlg(args.ip)
    gui.show()
    sys.exit(app.exec_())


