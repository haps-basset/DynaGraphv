#!/usr/bin/env python

import asyncore
import socket
import logging
import ast
from graphviz import Digraph

class Server(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.logger = logging.getLogger('Server')
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        self.address = self.socket.getsockname()
        self.logger.debug('binding to %s', self.address)
        self.listen(5)

    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        if client_info is not None:
            self.logger.debug('handle_accept() -> %s', client_info[1])
            ServerHandler(client_info[0], client_info[1])

class ServerHandler(asyncore.dispatcher):

    def __init__(self, sock, address):
        asyncore.dispatcher.__init__(self, sock)
        self.logger = logging.getLogger('Client ' + str(address))
        self.data_to_write = []

    def writable(self):
        return bool(self.data_to_write)

    def handle_write(self):
        data = self.data_to_write.pop()
        sent = self.send(data[:1024])
        if sent < len(data):
            remaining = data[sent:]
            self.data.to_write.append(remaining)
        self.logger.debug('handle_write() -> (%d) "%s"', sent, data[:sent].rstrip())

    def display_graph(self,command):
        try:
            f = Digraph()
            f.attr(rankdir='LR', size='8,5')
            v = list(ast.literal_eval(command))
            if len(v)>1:
                if type(v[0]) == tuple:
                    print "tuple "+command
                    f.edges(list(ast.literal_eval(command)))
                elif type(v[0]) == str:
                    v=command.replace("(","").replace(")","").replace("\"","").split(",")
                    print v[0]
                    f.edge(v[0],v[1])
            f.view("/tmp/tmp.gv")
        except Exception , e:
            self.logger.debug("Error: %s -> >>>%s<<<",str(e), command)

    def handle_read(self):
        tmp = ""
        while True:
            data = self.recv(1)
            if not data: break
            if data == "\n": break
            tmp += data
        if "edge" in tmp:
            self.logger.debug('received command [%s]', tmp)
            self.data_to_write.insert(0, "Command [{}]\n".format(tmp))
            res = tmp.replace("edge","").lstrip().replace(" ","")
            if len(res) > 1:
                self.display_graph(res)
        else:
            self.logger.debug('received unknown command [%s]', tmp)
            self.data_to_write.insert(0, "Unknown Command [{}]\n".format(tmp))

    def handle_close(self):
        self.logger.debug('handle_close()')
        self.close()

def main():
    try:
        logging.basicConfig(level=logging.DEBUG, format='%(name)s:[%(levelname)s]: %(message)s')
        HOST = '0.0.0.0'
        PORT = 80
        s = Server((HOST, PORT))
        asyncore.loop()
    except KeyboardInterrupt:
        print "Server cancelled "

if __name__ == '__main__':
    main()
