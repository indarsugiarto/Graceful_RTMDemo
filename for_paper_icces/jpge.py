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
SPINN_HOST = '192.168.240.1'
SPINN_PORT = 17893
DEBUG_MODE = 0
DELAY_IS_ON = True
#DELAY_SEC = 0.1  # useful for debugging
DELAY_SEC = 0.0001  # for release mode


NUM_PROC_BLOCK_VGA = 3550
NUM_PROC_BLOCK_SVGA = 5540
NUM_PROC_BLOCK_XGA = 9090


from PyQt4 import Qt, QtCore, QtNetwork
import sys
import struct
import argparse
import time
import os


class cEncoderTester(QtCore.QObject):
    def __init__(self, imgFile, wImg, hImg, numProcBlock, SpiNN, parent=None):
        super(cEncoderTester, self).__init__(parent)

        self.fName = imgFile
        self.wImg = wImg
        self.hImg = hImg
        self.numProcBlock = numProcBlock
        self.SpiNN = SpiNN

        # prepare the sdp receiver
        self.setupUDP()


    def setupUDP(self):
        self.sdpRecv = QtNetwork.QUdpSocket(self)
        print "[INFO] Trying to open UDP port-{}...".format(SDP_SEND_RESULT_PORT),
        ok = self.sdpRecv.bind(SDP_SEND_RESULT_PORT)
        if ok:
            print "done!"
            self.sdpRecv.readyRead.connect(self.readSDP)
            self.fmt = '<4I' # read SCP part (16 byte), don't care about cmd_rc and seq
            self.szData = struct.calcsize(self.fmt)
        else:
            print "fail!"

    @QtCore.pyqtSlot()
    def readSDP(self):
        """
        In this script, we just want to know the processing time reported by SpiNNaker program
        """
        while self.sdpRecv.hasPendingDatagrams():
            sz = self.sdpRecv.pendingDatagramSize()
            # NOTE: readDatagram() will produce str, not bytearray
            datagram, host, port = self.sdpRecv.readDatagram(sz)
            ba = bytearray(datagram)

        # remove the first 10 bytes of SDP header
        del ba[0:10]
        if len(ba) == self.szData:
            cmd, tmeas, arg2, arg3 = struct.unpack(self.fmt, ba)
            print "[INFO] Processing time = {} usec".format(tmeas)
            self.isRunning = False
        else:
            self.ackRecv = True

    def sendImgInfo(self):
        dpc = (SDP_RECV_RAW_INFO_PORT << 5) + SDP_RECV_CORE_ID  # destination port and core
        pad = struct.pack('2B', 0, 0)
        hdr = struct.pack('4B2H', 7, 0, dpc, 255, 0, 0)
        scp = struct.pack('2H3I', SDP_CMD_INIT_SIZE, self.numProcBlock, len(self.orgImg), self.wImg, self.hImg)
        sdp = pad + hdr + scp
        CmdSock = QtNetwork.QUdpSocket()
        CmdSock.writeDatagram(sdp, QtNetwork.QHostAddress(self.SpiNN), SPINN_PORT)
        CmdSock.flush()
        # then give a break, otherwise spinnaker might collapse
        #self.delay()

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
        CmdSock.writeDatagram(sdp, QtNetwork.QHostAddress(self.SpiNN), SPINN_PORT)
        CmdSock.flush()
        # then give a break, otherwise spinnaker will collapse
        self.delay()

    def delay(self):
        if DELAY_IS_ON:
            time.sleep(DELAY_SEC)

    def sendImgData(self):
        """
        Note: udp packet is composed of these segments:
              mac_hdr(14) + ip_hdr(20) + udp_hdr(8) + sdp + fcs(4)
              hence, udp_payload = 14+20+8+4 = 46 byte
        """
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


    def run(self):
        """
        Event main loop is here
        """
        # load data from image file
        print "[INFO] Loading image file...",
        with open(self.fName, "rb") as bf:
            self.orgImg = bf.read()     # read the whole file at once
        print "done!"

        # First send the image info to SpiNNaker and wait until ack is received
        self.ackRecv = False
        print "[INFO] Sending image info to SpiNNaker...",
        self.sendImgInfo()
        while self.ackRecv is False:
            QtCore.QCoreApplication.processEvents()
        print "done!"

        # Then send image data 
        self.sendImgData()

        self.isRunning = True
        while self.isRunning: #wait until SpiNNaker sends the result
            try:
                QtCore.QCoreApplication.processEvents()
            except KeyboardInterrupt:
                break

        sys.exit(0)


# ---------------------------- end of class cViewerDlg -----------------------------------


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Encoding JPG in SpiNNaker')
    parser.add_argument("imgFile", type=str, help="Raw gray image file (use creating_raw_data_from_jpg_image tools!)")
    parser.add_argument("imgSize", type=str, help="Image size. Valid value: vga, svga, xga")
    """
    parser.add_argument("wImg", type=int, help="Image width")
    parser.add_argument("hImg", type=int, help="Image height")
    """
    parser.add_argument("-ip", type=str, help="ip address of SpiNNaker")
    args = parser.parse_args()
    if args.ip is None:
        args.ip = SPINN_HOST

    if args.imgSize.upper() == "VGA":
        wImg = 640
        hImg = 480
        numProcBlock = NUM_PROC_BLOCK_VGA
    elif args.imgSize.upper() == "SVGA":
        wImg = 800
        hImg = 600
        numProcBlock = NUM_PROC_BLOCK_SVGA
    elif args.imgSize.upper() == "XGA":
        wImg = 1024
        hImg = 768
        numProcBlock = NUM_PROC_BLOCK_XGA
    else:
        print "Unsuported image size!"
        sys.exit(-1)

    app = Qt.QApplication(sys.argv)
    tst = cEncoderTester(args.imgFile, wImg, hImg, numProcBlock, args.ip)
    tst.run()
    sys.exit(app.exec_())


