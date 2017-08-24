#!/usr/bin/python

"""
This script is for stopping other script that runs a certain TCP port. It tries to make a TCP connection to the target script, and the target when recognize the request on the specified port will terminate gracefully.
"""

from PyQt4 import Qt, QtCore, QtNetwork
import argparse
import sys

defPortList = [40000, 40001]

class cKiller(QtCore.QObject):
    def __init__(self, port, parent=None):
        super(cKiller, self).__init__(parent)
        if port is not None:
            self.port = [port]
        else:
            self.port = defPortList

    @QtCore.pyqtSlot()
    def tcpConnected(self):
        self.tcp.disconnectFromHost()
        self.isRunning = False

    def run(self):
        self.isRunning = True
        print "[INFO] Try to close the script running the port-{}...".format(self.port),

        self.tcp = [QtNetwork.QTcpSocket(self) for _ in range(len(self.port))]
        for p in range(len(self.port)):
            self.tcp[p].connectToHost(QtNetwork.QHostAddress.LocalHost, self.port[p])
		    #p.connected.connect(self.tcpConnected)
		    
        """
	    while self.isRunning: #wait until SpiNNaker sends the result
	        try:
	            QtCore.QCoreApplication.processEvents()
	        except KeyboardInterrupt:
	            break
        if self.isRunning:
            print "fail!"
        else:
            print "done!"
        """
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stop the script running on certain TCP port. Use this script to other script that runs a certain TCP port.')
    parser.add_argument("-p","--port", type=int, help="the TCP port")
    args = parser.parse_args()

    app = Qt.QApplication(sys.argv)
    killer = cKiller(args.port, app)
    killer.run()
    sys.exit(app.exec_())

