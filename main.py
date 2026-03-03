import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

import cogs.database_helper as database_helper

# ========== START =========== #


intents = discord.Intents.all()

print(discord.__version__)

load_dotenv()
bot_token = os.environ['bot_token']

bot = commands.Bot(command_prefix="&", intents=intents, help_command=None)


# ========== STATIC VARIABLES =========== #


bot_token = os.environ['bot_token']
test_guilds = [901904937930346567]
owner_id = 336475402535174154
# test_guilds = None


# ========== ON READY =========== #


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}\n")

    print("====== BOT STARTED ======")

    for cog in bot.cogs:
        for command in bot.get_cog(cog).get_commands():
            print(command.name)
    print([guild.id for guild in bot.guilds])


# ========== LOADING COGS =========== #


if __name__ == '__main__':
    print("loading plugins...")
    """
    Loads the cogs from the `./cogs` folder.
    Note:
        The cogs are named in this format `{cog_dir}.{cog_filename_without_extension}`.
    """
    for cog in os.listdir('cogs'):
        if cog.endswith('.py') is True:
            print(f"loading cogs.{cog[:-3]}...")
            bot.load_extension(f'cogs.{cog[:-3]}')
        elif os.path.isdir(f'cogs/{cog}'):
            for file in os.listdir(f'cogs/{cog}'):
                if file.endswith('.py') is True:
                    print(f"loading cogs.{cog}.{file[:-3]}...")
                    bot.load_extension(f'cogs.{cog}.{file[:-3]}')


# ========== DISCORD =========== #


@bot.event
async def on_message(message):

    if message.author.bot is True:
        return

    await bot.process_commands(message)


# ========== SLASH COMMANDS =========== #

# @bot.slash_command(name="test_buttons", guild_ids=test_guilds)
# async def test_buttons(ctx):
#     buttons = discord.ui.View(timeout = None)
#     async def dice_buttons_callback(interaction):
#         await interaction.response.send("you clicked the button!")

#     for i in range(6):
#         button = discord.ui.Button(
#             label=i,
#             emoji='<:Miligo:881546316684091432>',
#             style=discord.ButtonStyle.gray
#         )
#         button.callback = dice_buttons_callback

#         buttons.add_item(button)
#     await ctx.respond(view=buttons)


# @bot.slash_command(name="test_select", guild_ids=test_guilds)
# async def test_selects(ctx):
#     select = discord.ui.Select()
#     for i in range(6, 12):
#         select.add_option(label=i)
#     await ctx.respond(view=discord.ui.View(select))


@bot.slash_command(name="games")
async def list_games(ctx):
    """Shows a list of available games"""
    description = ""
    for file in os.listdir('./cogs/games'):
        if file.endswith('.py') is True:
            description += (f'• {file[:-3]}\n')
    embed = discord.Embed(title="Available games", description=description, color=discord.Color.teal())
    await ctx.respond(embed=embed)


@bot.slash_command(name="set_category_channel")
async def select_game_hub_category(ctx, category: discord.commands.Option(discord.CategoryChannel, "Category, where all games will be played")):    # type: ignore
    """Used to set a category channel, where all games will be played"""
    if ctx.author.guild_permissions.manage_channels or ctx.author.guild_permissions.administrator:
        await database_helper.set_guild_config(ctx.guild.id, category.id)
        description = f"Game category channel has been set to `{category.name}`.\nFrom now on, all the games will be held in that category."
        embed = discord.Embed(title="Success!", description=description, color=discord.Color.green())
        await ctx.respond(embed=embed)
    else:
        description = "You don't have permission to change the category channel!"
        embed = discord.Embed(title="Access Denied!", description=description, color=discord.Color.red())
        await ctx.respond(embed=embed, ephemeral=True)

# @bot.slash_command(name="test", guild_ids=test_guilds)
# async def test(ctx, category: discord.CategoryChannel):
#     await ctx.respond(f"This is a test!!!")


# ========== TEXT COMMANDS =========== #


@bot.command(name="reload", description="Used to reload the bot. ONLY THE OWNER CAN USE THIS!", hidden=True)
@commands.is_owner()
async def reload_cogs(ctx):
    print("reloading...")
    for cog in os.listdir('./cogs'):
        if cog.endswith('.py') is True:
            bot.reload_extension(f'cogs.{cog[:-3]}')
        elif os.path.isdir(f'./cogs/{cog}'):
            for file in os.listdir(f'./cogs/{cog}'):
                if file.endswith('.py') is True:
                    bot.reload_extension(f'cogs.{cog}.{file[:-3]}')
    await ctx.send("Successfully reloaded all plugins!")


@bot.command(name="load", description="Used to manually load the bot. ONLY THE OWNER CAN USE THIS!", hidden=True)
@commands.is_owner()
async def load_cogs(ctx):
    print("loading...")
    for cog in os.listdir('./cogs'):
        if cog.endswith('.py') is True:
            print(f"loading cogs.{cog[:-3]}...")
            bot.load_extension(f'cogs.{cog[:-3]}')
        elif os.path.isdir(f'./cogs/{cog}'):
            for file in os.listdir(f'./cogs/{cog}'):
                if file.endswith('.py') is True:
                    print(f"loading cogs.{cog}.{file[:-3]}...")
                    bot.load_extension(f'cogs.{cog}.{file[:-3]}')
    await ctx.send("Successfully loaded all plugins!")


bot.run(bot_token)
