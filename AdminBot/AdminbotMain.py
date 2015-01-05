from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from LoggingMain import LoggingMain
import time
import sys
import datetime


class AdminBotMain(protocol.ClientFactory):

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def buildProtocol(self, addr):
        p = AdminBot()
        p.factory = self
        return p

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        connector.connect()


class AdminBot(irc.IRCClient):

    nickname = "fossasia-guard"
    chanOps = []
    badWords = []

    NickServPASS = "sample"
    voiceOnlyMode = False  # do not change

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = LoggingMain(open(self.factory.filename, "a"))
        self.logger.log(
            "[connected at %s]" %
            time.asctime(
                time.localtime(
                    time.time())))

    def signedOn(self):
        self.join(self.factory.channel)
        z = open("ops.txt")
        self.chanOps = z.read().splitlines()
        z.close()
        z = open("bad_words.txt")
        self.badWords = z.read().splitlines()
        z.close()
        self.msg("NickServ", self.NickServPASS)

    def kickedFrom(self, channel, kicker, message):
        self.logger.log("[%s kicked me... %s]" % (kicker, message))
        self.msg(kicker, "Hi, please do not kick me. I am there to help.")
        self.join(channel)

    def joined(self, channel):
        self.logger.log("[Joined %s]" % channel)
        self.say(
            self.factory.channel,
            "Hi everybody, I am bot created by Tymon Radzik ! I am there to help you and fight all the spammers. If you need help, just write '!help'")

    def userJoined(self, user, channel):
        if user not in self.chanOps:
            self.msg(
                user,
                "Hello, welcome on #fossasia IRC channel, I am guard bot there. Don't ask to ask, just ask :D If you need help please write \"!help\" on channel. Please keep in mind netiquette rules, while talking there!")
        self.logger.log("[%s joined %s]" % (user, channel))

    def action(self, user, channel, data):
        self.logger.log("[%s does %s]" % (user, data))

    def userLeft(self, user, quitMessage):
        self.logger.log("[%s left with msg: %s]" % (user, quitMessage))

    def userQuit(self, user, message):
        self.logger.log("[%s left channel]" % user)

    def userRenamed(self, oldname, newname):
        self.logger.log("[%s changed nick to %s]" % (oldname, newname))

    def userKicked(self, kickee, channel, kicker, message):
        self.logger.log(
            "[%s has been kicked from %s by %s with msg: %s]" %
            (kickee, channel, kicker, message))

    def noPerms(self, user, command):
        self.logger.log(
            "[%s tried to run \" %s \" command. Denied.]" %
            (user, command))
        self.say(
            self.factory.channel,
            "Hi, %s, it seems you can't run admin commands on this channel!" %
            user)

    def privmsg(self, user, channel, message):
        user = user.split('!')[0]

        # deny disscussions on priv, except commands send by chanOps
        if channel == self.nickname and user not in self.chanOps:
            self.msg(
                user,
                "Hi, if you don't know, I am guard bot here. Please do not talk with me on priv, use main channel instead")
            self.logger.log("[%s wrote to me on priv: %s]" % (user, message))
            return

        # message starts with ! = send a command
        if message.startswith("!"):
            args = message.split(" ")
            if args[0] == "!help":
                self.logger.log(
                    "[%s asked for help with %s command]" %
                    (user, message))
                self.say(
                    channel,
                    "Hi %s, this is #FOSSASIA channel on IRC. If you need help from any of owners, please write '!admins' and they will try to answer ASAP. If you have any questions - just ask :D To get list of available commands, write: '!cmdlist'" %
                    user)
                return
            elif args[0] == "!admins":
                self.logger.log(
                    "[%s asked admins for help with %s command]" %
                    (user, message))
                for admin in self.chanOps:
                    self.logger.log("%s" % admin)
                    self.msg(
                        admin,
                        "Howdy admin! %s asked you for fast-help on %s. Please reply him ASAP. Thx" %
                        (user,
                         channel))
                    self.logger.log("[sent help request to %s]" % admin)
                self.msg(
                    user,
                    "Admins has been asked for help... Explain them your problem, as accurate as you only can")
                return

            elif args[0] == "!cmdlist":
                self.logger.log(
                    "[%s run %s command to get cmdlist]" %
                    (user, message))
                self.say(
                    channel,
                    "%s: available commands are: !help !admin !cmdlist || Ops also have access to: !topic !kick !ban !mute !unmute !unban !voice !unvoice !voiceonly" %
                    user)
                return

            # end of normal user commands
            # deny permissions to next ones
            elif user not in self.chanOps:
                self.noPerm(user, message)
                return

            elif args[0] == "!kick":
                if len(args) < 2:
                    self.logger.log(
                        "[%s asked to kick, without giving all neccesary args]" %
                        user)
                    self.msg(
                        user,
                        "Hi guy, you haven't provided all neccessary arguments to !kick command. It should be !kick USER [REASON]")
                    return

                if len(args) < 3:
                    self.kick(channel, args[1], "%s wanted that" % user)
                    self.logger.log(
                        "[%s told me to kick %s without reason]" %
                        (user, args[1]))
                else:
                    self.kick(channel, args[1], "%s: %s" % (user, args[2]))
                    self.logger.log(
                        "[%s told me to kick %s with reason %s]" %
                        (user, args[1], args[2]))
                return

            elif args[0] == "!voiceonly":
                self.voiceOnlyMode = not self.voiceOnlyMode
                self.mode(channel, self.voiceOnlyMode, 'm')
                for admin in self.chanOps:
                    self.mode(channel, self.voiceOnlyMode, 'v', user=admin)
                self.logger.log(
                    "[%s changed voiceOnlyMode var to %s]" %
                    (user, self.voiceOnlyMode))
                return

            elif args[0] == "!voice":
                self.logger.log(
                    "[%s run command to give voice: %s]" %
                    (user, message))
                if len(args) < 2:
                    self.msg(
                        user,
                        "You have to provide the nick of user, you want to give voice for")
                    return
                self.mode(channel, True, 'v', user=args[1])
                return

            elif args[0] == "!unvoice":
                self.logger.log(
                    "[%s ran command to unvoice: %s]" %
                    (user, message))
                if len(args) < 2:
                    self.msg(user, "Who do you want to devoice?")
                    return
                self.mode(channel, False, 'v', user=args[1])
                return

            elif args[0] == "!ban":
                self.logger.log("[%s told to ban: %s]" % (user, message))
                if len(args) < 2:
                    self.msg(user, "Who do you want to ban?")
                    return
                self.mode(channel, True, 'b', user=args[1])

            elif args[0] == "!unban":
                self.logger.log("[%s told to unban: %s]" % (user, message))
                if len(args) < 2:
                    self.msg(
                        user,
                        "Maybe you will tell me who do you want to unban?")
                    return
                self.mode(channel, False, 'b', user=args[1])

            elif args[0] == "!mute":
                self.logger.log("[%s want to mute: %s]" % (user, message))
                if len(args) < 2:
                    self.msg(user, "Who do you want to mute?")
                    return
                self.mode(channel, True, 'q', user=args[1])

            elif args[0] == "!unmute":
                self.logger.log("[%s wants to unmute: %s]" % (user, message))
                if len(args) < 2:
                    sel.msg(user, "Who do you want to unmute?")
                    return
                self.mode(channel, False, 'q', user=args[1])

            else:
                self.logger.log(
                    "[%s wants to change topic: %s]" %
                    (user, message))
                if len(args) < 2:
                    sel.msg(user, "Maybe give us this topic???")
                    return
                topic = ""
                for x in range(1, len(args)):
                    topic = topic + args[x] + " "
                self.topic(channel, topic)
                return
            return

        # this is called when admins tell something to bot on priv, but that
        # isn't a command
        if channel == self.nickname:
            self.say(
                user,
                "Hi, please do not interrupt me, sending text, which isn't a command")
            self.logger.log(
                "[%s who is admin send to me message on priv : %s]" %
                (user, message))
            return

        # user send normal message to channel
        self.logger.log("%s: %s" % (user, message))
        # check does message contain any bad word
        if any(t_msg in message for t_msg in self.badWords):
            # ops can use bad words...
            if user not in self.chanOps:
                self.kick(channel, user, "Using bad-words")
                self.msg(
                    user,
                    "You have been kicked, because you tried to use prohibited words on this channel! Do not do that anymore, otherwise you might get banned")
                self.logger.log(
                    "[I have kicked %s, because he used bad-words]" %
                    user)

        return
