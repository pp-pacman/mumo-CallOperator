#!/usr/bin/env python
# -*- coding: utf-8

# Copyright (C) 2016 Frank Fitzke <pp-pacman@gmx.de>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the Mumble Developers nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# `AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# CallOperator.py
# This module realize a OperatorCall by the Twitter Message Service. Any user can initiate
# a OperatorCall. In the Context_Menue there is a new Entry. If an User click this Item a list of Operators gets
# a Message with Informations about the calling user, the Servername, the channelname and the marked user.
#

from mumo_module import (commaSeperatedIntegers,
                         MumoModule)
import cgi

#from Ice import Logger
import Ice

import logging
#import thread
import threading
from threading import Timer
import re

import twitter


class TwitterObject(object):

    def __init__(self, configobj, log):
#        threading.Thread.__init__(self)
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug('ttt:' + repr(configobj.CONSUMER_KEY))

        self.api = twitter.Api(configobj.CONSUMER_KEY,
             configobj.CONSUMER_SECRET,
             configobj.ACCESS_TOKEN,
             configobj.ACCESS_TOKEN_SECRET)

        log.debug("server started")


class CallOperatorWorker(threading.Thread):

   def __init__(self, configobj, server, twitterchannel):
        threading.Thread.__init__(self)
        self.log = logging.getLogger(self.__class__.__name__)
        self.server = server
        self.twitterchannel = twitterchannel


        if (len(configobj.RECIPIENTS) > 0):
            recipientslist = configobj.RECIPIENTS.split(",")
            self.recipients = []
            for recipient in recipientslist:
                recipient = recipient.strip()
                if recipient.startswith("@"):
                    self.recipients.append(recipient)
                else:
                    self.log.error("recipients must start with @")
        else:
            self.recipients = []

        self.log.debug(repr(self.recipients))

        if (self.twitterchannel is not -1):
            # Channelid suchen
            self.twitterchannel = twitterchannel


   def run(self):
       self.watchdog = Timer(10, self.endvote).start()
       self.log.debug('TEST - TEST - TEST - TEST')
#       self.log.debug(repr(self.server.getAllConf()))
       self.log.debug("Server name: " + self.server.getConf('registername'))
       for recipient in self.recipients:
           self.log.debug(" recipient: " + recipient)


   def endvote(self):
       self.log.debug('aaa  TEST - TEST - TEST - TEST')
#       votekickaction.log.debug('endvote')
#       self.callop(server,)

   def callop(self, server, user, target):
       if (self.twitterchannel < 0):
           return
       self.log.debug("Calling Twitter")

       text = ""
       text += "CallOperator: "

       self.log.debug(repr(server.getChannels()[0]))

       servername = str(server.getConf('registername'))

       callinguser = str(user.name)
       rougeuser = str(target.name)
       channelname = str(server.getChannels()[target.channel].name)

       text += "" + callinguser + " on " + servername + " calls an operator in behave of user " + rougeuser + " on channel " + channelname

       for recipient in self.recipients:
           result = self.twitterchannel.api.PostDirectMessage(text[:140],None,recipient)
           self.log.debug(repr(result))

class CallOperator(MumoModule):

    default_config = {'CallOperator':(('servers', commaSeperatedIntegers, []), ),
                        lambda x: re.match('(twitter_\d+)', x):(
                            ('CONSUMER_KEY',        str, ""),
                            ('CONSUMER_SECRET',     str, ""),
                            ('ACCESS_TOKEN',        str, ""),
                            ('ACCESS_TOKEN_SECRET', str, "")
                        ),
                        lambda x: re.match('(worker_\d+)', x):(
                            ('SERVERID',            str, "1"),
                            ('TWITTERCHANNEL',      int, -1),
                            ('RECIPIENTS',          str, "")
                        )
                     }


    def __init__(self, name, manager, configuration = None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()
        self.action_callop =  manager.getUniqueAction()
        log = self.log()
        log.debug("ssss")

        counter = 1
        CallOperator.twitterchannels = {}
        scfg = 0
#        log.debug("Starting #")
        while (not (scfg is None)):
#            log.debug("Starting ## " + str(counter))
            try:
                scfg = getattr(self.cfg(), 'twitter_%d' % counter)
            except AttributeError:
                scfg = None
                log.debug("Starting failed " + str(counter))
                break
            log.debug("Starting Twitterchannel " + str(counter))
            log.debug("sss:" + repr(scfg.CONSUMER_KEY))

            CallOperator.twitterchannels[counter] = TwitterObject(scfg, log)
#            twitterstream.twitterchannels[counter].start()

            counter = counter + 1

        self.threads = []

   # Fall back to ret
                                                                                                                                                             
    def connected(self):
        manager = self.manager()
        log = self.log()
        log.debug("Register for Server callbacks")

        servers = self.cfg().CallOperator.servers
        if not servers:
            servers = manager.SERVERS_ALL

        self.log().debug("servers ::: " + repr(servers))
        manager.subscribeServerCallbacks(self, servers)


        connServers = manager.getMeta().getBootedServers();


        for serv in connServers:

            try:
                scfg = getattr(self.cfg(), 'worker_%d' % serv.id())
            except AttributeError:
                scfg = None

            if ( scfg is None):
                return

            log.debug("Starting Worker " + str(serv.id()))

            thread = CallOperatorWorker(scfg, serv, CallOperator.twitterchannels[scfg.TWITTERCHANNEL])
            self.threads += [thread]
            thread.start()



    def disconnected(self):
        self.log().info(" triggered removal")

    def __exit__(self, exc_type, exc_value, traceback):
        self.log().info(" triggered removal")

    def __on_callop(self, server, action, user, target):
        assert action == self.action_callop
        self.log().info(user.name + " called an operator on behalf of " + str(target));


        entry = "%i-%s" % (server.id(), user.name)

        self.log().debug("worker count " + repr(len(self.threads)))

        for worker in self.threads:
            #self.log().debug("x:" + repr(worker.server.id()))
            if (worker.server.id() == server.id()):
                self.log().debug("Worker gefunden")
                worker.callop(server, user, target)

    def userConnected(self, server, user, context = None):
        # Adding the entries here means if mumo starts up after users
        # already connected they won't have the new entries before they
        # reconnect. You can also use the "connected" callback to
        # add the entries to already connected user. For simplicity
        # this is not done here.

        manager = self.manager()

        manager.addContextMenuEntry(
                server,
                user,
                self.action_callop,
                "CallOperator",
                self.__on_callop,
                self.murmur.ContextUser
        )

    def userDisconnected(self, server, state, context = None):
#        self.deleteusers(server, state, self.users)
#        self.log().debug("triggered userDisconnected: " + repr(state))
        pass

    def userStateChanged(self, server, state, context = None):
#        self.updateusers(server, state, self.users)
#        self.log().debug("triggered userStateChanged: " + repr(state))
        pass

    def userTextMessage(self, server, user, message, current=None): pass
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass
