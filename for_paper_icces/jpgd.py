#!/usr/bin/python

"""
Experiment procedure:
- sent a jpg image to spinnaker
- spinnaker send the processing time as an sdp message

"""

DEF_SPINN_IP = '192.168.240.1'
SPINN_CHIP_X = 0
SPINN_CHIP_Y = 0
SPINN_PORT = 17893


#/*--- For JPEG file ---*/
SDP_PORT_JPEG_DATA = 1
SDP_PORT_JPEG_INFO	 = 2
#/*--- For Raw RGB file ---*/
SDP_PORT_RAW_DATA    = 3
SDP_PORT_RAW_INFO   = 4
#/*--- For both ---*/
SDP_CMD_INIT_SIZE	= 1
SDP_CMD_CLOSE_IMAGE	= 2
SDP_CMD_REPORT_TMEAS  =  3

SDP_RECV_CORE_ID = 2	

SDP_SEND_RESULT_TAG = 1
SDP_SEND_RESULT_PORT = 30000


DELAY_IS_ON = True
DELAY_SEC = 0.01


from PyQt4 import Qt, QtCore, QtNetwork
import struct
import argparse
import time
import sys

class cDecoderTester(QtCore.QObject):
    def __init__(self, imgFile, SpiNN, parent=None):
        super(cDecoderTester, self).__init__(parent)

        self.imgFile = imgFile
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
        CmdSock.writeDatagram(sdp, QtNetwork.QHostAddress(self.SpiNN), SPINN_PORT)
        return sdp

    def sendImgInfo(self, szFile):
        f = 7 #no reply
        t = 0
        dp = SDP_PORT_JPEG_INFO
        dc = SDP_RECV_CORE_ID
        dax = SPINN_CHIP_X
        day = SPINN_CHIP_Y
        cmd = SDP_CMD_INIT_SIZE
        seq = 0
        arg1 = szFile
        arg2 = 0
        arg3 = 0
        self.sendSDP(f,t,dp,dc,dax,day,cmd,seq,arg1,arg2,arg3,None)


    def sendChunk(self, chunk):
        # based on sendSDP()
        # will be sent to chip <0,0>, no SCP
        dpc = (SDP_PORT_JPEG_DATA << 5) + SDP_RECV_CORE_ID  # destination port and core
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
        #iterate until all data in self.orgImg is sent
        szImg = len(self.orgImg)    # length of original data
        print "[INFO] Start sending raw image data of {}-bytes to SpiNNaker...".format(szImg)
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
            self.sendChunk(chunk)
            szRem -= szSDP
            sPtr = ePtr
            ePtr += szSDP
        # finally, send EOF (end of image transmission)
        self.sendChunk(None)
        print "[INFO] All done! Waiting result..."
        

    def run(self):
        """
        Event main loop is here
        """
        # load data from image file
        print "[INFO] Loading image file...",
        with open(self.imgFile, "rb") as bf:
            self.orgImg = bf.read()     # read the whole file at once
        print "done!"

        # First send the image info to SpiNNaker and wait until ack is received
        self.ackRecv = False
        print "[INFO] Sending image info to SpiNNaker...",
        self.sendImgInfo(len(self.orgImg))
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Decoding JPG in SpiNNaker')
    parser.add_argument("jpgInput", type=str, help="JPG input file")
    parser.add_argument("-ip", type=str, help="ip address of SpiNNaker")
    args = parser.parse_args()

    if args.ip is None:
        args.ip = DEF_SPINN_IP

    app = Qt.QApplication(sys.argv)
    decTester = cDecoderTester(args.jpgInput, args.ip)
    decTester.run()
    sys.exit(app.exec_())

