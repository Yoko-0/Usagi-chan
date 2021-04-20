import discord, asyncio, time, shelve, datetime, sys, os
from threading import Thread
from src.functions import newLog, loadConfig, getLogger
from src.extraClasses.classMember import Members
from src.extraClasses.DB import Database
from src.extraClasses.musicPlayer import MusicPlayer
from src.extraClasses.Token import Token
from src.guildCommands.autoRemoveRequest import autoRemoveRequest
from src.privatCommands.updateShedule import checkNotification

async def checkRequests():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(autoRemoveRequest(usagi), usagi.loop)


async def checkShedule():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(checkNotification(usagi), usagi.loop)

def checkAudio():
    while True:
        time.sleep(5)
        usagi.musicPlayer.checkPlay()

async def checkTokens():
    while True:
        time.sleep(5)
        asyncio.run_coroutine_threadsafe(usagi.token.checkTokens(usagi), usagi.loop)



class UsagiChan:

    def __init__(self):
        self.config = loadConfig('src/config')
        self.loop = None
        intents = discord.Intents.all()
        self.client = discord.Client(intents = intents)
        self.LOGGER = getLogger()
        self.members = Members(self.config['data']['guildId'])
        self.db = Database(self)
        self.musicPlayer = MusicPlayer()
        self.token = Token()
        if not os.path.exists('files/Downloads'):
            os.mkdir('files/Downloads')
        os.chdir('files/Downloads')

    def checkConnection(self):
        @self.client.event
        async def on_ready():

            self.LOGGER.info('Successfully connected to discord')
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game("ver 1.0.0.1.5 | Всё ещё учится работать |"))
            self.loop = asyncio.get_event_loop()
            await self.members.fillMembers(self.client)

    def run(self):
        self.client.run(self.config['data']['token'])


    from events.newMessageEvent import setMessageEvent
    from events.voiceStateUpdateEvent import setVoiceStateUpdateEvent
    from events.newReactionEvent import setNewReactionEvent
    from events.removeReactionEvent import setRemoveReactionEvent
    from events.usersChangedEvents import setUsersChangedEvents



usagi = UsagiChan()
usagi.checkConnection()
usagi.setMessageEvent()
usagi.setVoiceStateUpdateEvent()
usagi.setNewReactionEvent()
usagi.setRemoveReactionEvent()
usagi.setUsersChangedEvents()



newLog('', '', '', '', new = 1)
Thread(target=asyncio.run, args=(checkRequests(), )).start()
Thread(target=asyncio.run, args=(checkShedule(), )).start()
Thread(target=checkAudio).start()
Thread(target=asyncio.run, args=(checkTokens(), )).start()
usagi.run()
