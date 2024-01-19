from replit import db
import os

def initialize_database(bot):
    #DB->PERMITTED
    if 'permitted' not in db.keys():
        db['permitted'] = [336475402535174154]
        print("««« CREATED DIRECTORY __DB->PERMITTED__ INTO DATABASE »»»")
    
    #DB->GAMES
    if 'games' not in db.keys():
        db['games'] = dict()
        print("««« CREATED DIRECTORY __DB->GAMES__ INTO DATABASE »»»")

    #DB->GAMES->[GAME_NAMES]
    for game in os.listdir('./cogs/games'):
        if game.endswith('.py') and f'{game[:-3]}' not in db['games'].keys():
            db['games'][f'{game[:-3]}'] = dict()
            print(f"««« CREATED DIRECTORY __DB->GAMES->{game[:-3]}__ INTO DATABASE »»»")

    for game in db['games']:
        #DB->GAMES->game->GLOBAL_HIGHSCORES
        if 'global_highscores' not in db['games'][game].keys():
            db['games'][game]['global_highscores'] = dict()
            print(f"««« CREATED DIRECTORY __DB->GAMES->{game}->GLOBAL_HIGHSCORES__ INTO DATABASE »»»")

    #DB->GUILDS
    if 'guilds' not in db.keys():
        db['guilds'] = dict()
        print("««« CREATED DIRECTORY __DB->GUILDS__ INTO DATABASE »»»")

    #DB->GUILDS->[GUILD_IDS]
    for guild in bot.guilds:
        if str(guild.id) not in db['guilds'].keys():
            db['guilds'][str(guild.id)] = dict()
            print(f"««« CREATED DIRECTORY __DB->GUILDS->{guild.id}__ INTO DATABASE »»»")

    for guild in db['guilds']:
        #DB->GUILDS->guild->GAMES
        if 'games' not in db['guilds'][guild].keys():
            db['guilds'][guild]['games'] = dict()
            print(f"««« CREATED DIRECTORY __DB->GUILDS->{guild}->GAMES__ INTO DATABASE »»»")

        for game in db['games']:
            #DB->GUILDS->guild->GAMES->[GAME_NAMES]
            if game not in db['guilds'][guild]['games'].keys():
                db['guilds'][guild]['games'][game] = dict()
                print(f"««« CREATED DIRECTORY __DB->GUILDS->{guild}->GAMES->{game}__ INTO DATABASE »»»")

            #DB->GUILDS->guild->GAMES->game->HIGHSCORES
            if 'highscores' not in db['guilds'][guild]['games'][game].keys():
                db['guilds'][guild]['games'][game]['highscores'] = dict()
                print(f"««« CREATED DIRECTORY __DB->GUILDS->{guild}->GAMES->{game}->HIGHSCORES__ INTO DATABASE »»»")
