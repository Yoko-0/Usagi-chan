import logging.config

logChannel = 803634355305709568
#messageChannel = 734004322177646614
requestChannel = 803634355305709568

guildId = 733631069542416384
yokoId = 290166276796448768
botId = 801153197552304129
requestRoleID = 803362317978304512
puficonfaId = 733631069542416384

moviegoers = [yokoId, 289485158153715713]

token = 'ODAxMTUzMTk3NTUyMzA0MTI5.YAciDw.Gm9x7NeXHvUrJvLfJ-tmlbD9URs'


valentineThumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/801926601481912320/cbf89215894687f9f0e81aa7d125dba1_cupid-bow-arrow-hearts-cupid-heart-with-arrow-png-transparent-_860-.png'
requestThumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/803024394203955250/unknown.png'


privateCommands = {
    'createValentine': '!валентинка',
    'simpleMessageCommand': '!m',
    'deleteValentine': '!сотри',
    'updateShedule': '!обновить'}

guildCommands = {
    'createRequest': '!создать',
    'helpCommand': '!помощь'}

def getLogger():
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(name)s] %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": [
                "console"
            ]
        }
    })

    return logging.getLogger()
