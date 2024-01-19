import discord
# from discord.ext import commands
# from discord.errors import Forbidden
from replit import db
from discord.commands import SlashCommandGroup
import random
from sys import exc_info
# import time

dice_emoji = {1:'<:dice_1:755891608859443290>',2:'<:dice_2:755891608741740635>',3:'<:dice_3:755891608251138158>',4:'<:dice_4:755891607882039327>',5:'<:dice_5:755891608091885627>',6:'<:dice_6:755891607680843838>'}

# CLASSES #

class DiceButton(discord.ui.Button):
    # DiceButton INITIALIZATION
    def __init__(self, parent, label="", emoji=None, custom_id=None):
        self.parent = parent
        try:
            row = 0 if int(custom_id) <= 3 else 1
        except:
            row = None
        super().__init__(label=label, emoji=emoji, row=row)

    # DiceButton FUNCTIONS
    async def callback(self, interaction):
        self.style = discord.ButtonStyle.blurple if self.style == discord.ButtonStyle.gray else discord.ButtonStyle.gray
        await interaction.response.edit_message(view=self.parent)


class FarkleRoundView(discord.ui.View):
    # FarkleRoundView INITIALIZATION
    def __init__(self, ctx, dice, dice_remaining, round_score, game_scores, players, current_player_id, winning_score):
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.dice = dice
        self.dice_remaining = dice_remaining
        for key, val in dice.items():
            self.add_item(DiceButton(parent=self, emoji=val, custom_id=str(key+1)))
        self.round_score = round_score
        self.scoring_system = FarkleScoringSystem(self)
        self.game_scores = game_scores
        self.players = players
        self.current_player_id = current_player_id    # id of element in the self.players list
        self.current_player = players[current_player_id]
        self.winning_score = winning_score

    @discord.ui.button(label="Pass & score", emoji=None, style=discord.ButtonStyle.danger, row=2)
    async def stop_button_callback(self, button, interaction):
        for button in self.children:
            button.disabled = True
        await interaction.response.edit_message(view=self)
        
        if not self.scoring_system.score():
            self.round_score = 0
            await interaction.followup.send(f"**Bust!**\n{self.current_player.mention}, you got `{self.round_score}` points for this round :(")
            self.stop()
            return

        self.round_score += self.scoring_system.score()
        await interaction.followup.send(f"{self.current_player.mention}, you scored `{self.round_score}` points this round\nCongrats!")
        self.stop()
        return

    @discord.ui.button(label="Roll again", emoji=None, style=discord.ButtonStyle.green, row=2)
    async def continue_button_callback(self, button, interaction):    
        if not self.is_at_least_one_selected():
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("**You have to select at least one!**", ephemeral=True)
            return

        if not self.scoring_system.score():
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("**Every die must be scoring!**", ephemeral=True)
            return
            
        for button in self.children:
            button.disabled = True
        self.timeout = None
        await interaction.response.edit_message(view=self)
        if self.are_all_selected():
            self.dice_remaining = 6
        else:
            self.dice_remaining = self.dice_unselected_count()
        self.round_score += self.scoring_system.score()
        await self.roll_dice(interaction)
        

    async def interaction_check(self, interaction):
        if interaction.user != self.current_player:
            await interaction.response.send_message("Oi! Play your own game!", ephemeral=True)
            return False
        else:
            return True
        
    # FarkleRoundView FUNCTIONS
    def round_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title = f"**{self.players[0].name}** vs. **{self.players[1].name}** | First to {self.winning_score} points wins!",
            color = discord.Color.teal(),
            description = f"Game scores:\n{self.players[0].mention} - `{self.game_scores[0]}`\n{self.players[1].mention} - `{self.game_scores[1]}`\n\nRound score: `{self.round_score}`\nThese are your dice:"
        )
        embed.set_footer(text=f"{self.current_player.name}'s turn", icon_url=self.current_player.display_avatar.url)
        # content = "Game scores:\nPlayer 1 - `{self.game_scores['player1']}\nPlayer 2 - `{self.game_scores['player2']}`\n\nRound score: `{self.round_score}`\nThese are your dice:"
        return embed
    
    async def roll_dice(self, interaction):        
        self.dice = dict()
        for die_id in range(self.dice_remaining):
            self.dice[die_id] = dice_emoji[random.randint(1, 6)]
        round_embed = self.round_embed()
        round_view = FarkleRoundView(self.ctx, self.dice, self.dice_remaining, self.round_score, self.game_scores, self.players, self.current_player_id, self.winning_score)
        await interaction.followup.send(embed=round_embed, view=round_view)
        timed_out = await round_view.wait()
        self.round_score = round_view.round_score
        if timed_out:
            self.timeout = 0.1
            await interaction.edit_original_message(view=self)
        else:
            self.stop()
        
    def is_at_least_one_selected(self) -> bool:
        if len([button for button in self.children if button.style == discord.ButtonStyle.blurple]) > 0:
            return True
        else:
            return False

    def are_all_selected(self) -> bool:
        if len([button for button in self.children if button.style == discord.ButtonStyle.blurple]) == len(self.children)-2:
            return True
        else:
            return False

    def dice_unselected_count(self) -> int:
        return len([button for button in self.children if button.style == discord.ButtonStyle.gray])

    def dice_selected(self) -> list:
        return [button for button in self.children if button.style == discord.ButtonStyle.blurple]


class FarkleScoringSystem():
    def __init__(self, dice_buttons_view):
        self.dice_view = dice_buttons_view
        self.dice_faces_count = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0}

    def count_faces(self):
        self.dice_selected = self.dice_view.dice_selected()
        for i in range(1, 7):  
            self.dice_faces_count[i] = len([dice for dice in self.dice_selected if str(dice.emoji) == dice_emoji[i]])

    def score(self):
        self.count_faces()
        added_score = 0

        selected = [dice for dice in self.dice_faces_count if self.dice_faces_count[dice] >= 1]
        selected_twice = [dice for dice in self.dice_faces_count if self.dice_faces_count[dice] == 2]
        if len(selected) == 6:
            return 1500
        elif len(selected) == 5:
            if 1 in selected_twice:
                added_score += 100
            elif 5 in selected_twice:
                added_score += 50
            elif len(selected_twice) > 0:
                return 0    # There is a non-scoring dice outside of the combo (illegal move!)
            
            if 1 in selected and 6 not in selected:
                added_score += 500
                return added_score
            elif 1 not in selected and 6 in selected:
                added_score += 750
                return added_score
            else:
                return 0    # There is a hole inside of the combo (illegal move!) (eg. 1-2-4-5-6)
                
        else:
            for dice_face in self.dice_faces_count:
                times_dice_used = 0
                if self.dice_faces_count[dice_face] >= 3 and dice_face == 1:
                    added_score += 1000 * pow(2, self.dice_faces_count[dice_face]-3)
                    times_dice_used += self.dice_faces_count[dice_face]
                elif self.dice_faces_count[dice_face] >= 3:
                    added_score += 100 * dice_face * pow(2, self.dice_faces_count[dice_face]-3)    # double for each additional number over 3 of a kind
                    times_dice_used += self.dice_faces_count[dice_face]
                elif dice_face == 1:
                    added_score += 100 * self.dice_faces_count[dice_face]
                    times_dice_used += self.dice_faces_count[dice_face]
                elif dice_face == 5:
                    added_score += 50 * self.dice_faces_count[dice_face]
                    times_dice_used += self.dice_faces_count[dice_face]
    
                if times_dice_used != self.dice_faces_count[dice_face]:
                    return 0    # There is a non-scoring dice (illegal move!)
    
            return added_score

    
class AcceptChallengeView(discord.ui.View):
    def __init__(self, ctx, rival):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.denied = False
        self.rival = rival
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept_button_callback(self, button, interaction):
        for button in self.children:
            button.disabled = True
        await interaction.response.send_message("You accepted the invite!", ephemeral=True)
        await self.ctx.respond(f"{self.ctx.interaction.user.mention}! {interaction.user.mention} accepted the invite of playing Farkle with you!", ephemeral=True)
        await self.ctx.interaction.edit_original_message(content=f"{interaction.user.mention} accepted the invite from {self.ctx.interaction.user.mention} to a game of Farkle!", view=self)
        self.rival = interaction.user
        self.stop()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny_button_callback(self, button, interaction):        
        for button in self.children:
            button.disabled = True
        await interaction.response.send_message("You denied the invite!", ephemeral=True)
        await self.ctx.respond(f"{self.ctx.interaction.user.mention}! {interaction.user.mention} denied the invite of playing Farkle with you!", ephemeral=True)
        await self.ctx.interaction.edit_original_message(content=f"{self.rival.mention} denied the invite from {self.ctx.interaction.user.mention} to a game of Farkle!", view=self)
        self.denied = True
        self.stop()

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        if self.rival:
            await self.ctx.respond(f"{self.ctx.interaction.user.mention}! Invite of playing Farkle with {self.rival.mention} timed out!", ephemeral=True)
            await self.ctx.interaction.edit_original_message(content=f"{self.rival.mention}, invite from {self.ctx.interaction.user.mention} to a game of Farkle timed out!", view=self)
        else:
            await self.ctx.respond(f"{self.ctx.interaction.user.mention}! Open invite of playing Farkle timed out!", ephemeral=True)
            await self.ctx.interaction.edit_original_message(content=f"Open invite from {self.ctx.interaction.user.mention} to a game of Farkle timed out!", view=self)

    async def interaction_check(self, interaction):
        if interaction.user != self.rival and self.rival:
            await interaction.response.send_message("You cannot respond to someone else's invite!", ephemeral=True)
        return interaction.user == self.rival or not self.rival
        


class Farkle(discord.Cog):
    """
    Farkle commands
    """
    def __init__(self, bot):
        self.bot = bot
        
    farkle = SlashCommandGroup("farkle", "Commands connected with the game Farkle")

    
    # EVENTS

    @discord.Cog.listener()
    async def on_error(self, interaction):
        exc = exc_info()
        print(f"interacted failed for {interaction}")
        if interaction.is_component():
            print(interaction.data)
        try:
            interaction.respond(exc)
        except:
            try:
                user = await self.bot.fetch_user(336475402535174154)
                await user.send(exc)
            except:
                pass
                
        with open("/errors.txt", 'w') as f:
            f.write(exc)
            f.write("<<<================================>>>")
                
    
    
    # FUNCTIONS
    

        
    # COMMANDS
    
    @farkle.command(name="rules", brief="show the rules of Farkle")
    async def rules(self, ctx):
        """Shows rules of Farkle"""
        embed = discord.Embed(
            title="Rules of Farkle",
            color=discord.Color.teal()
        )
        embed.add_field(
            name="How to play", 
            value="""
            Farkle is a 2-player game, where the first one to reach winning_score points wins. 
            Both players take turns playing, and during the first round, a random person starts.
            At the first throw each turn, 6 dice are thrown. If you wish to throw again, you can do so by clicking `Continue`.
            On the next throw, you'll throw however many dice you had minus the amount selected, e.g. you threw 5 dice and selected 2, next you'll throw 3 dice.""", 
            inline=False
        )
        embed.add_field(
            name="One's turn ends either by:", 
            value="""
            • Passing the turn by submitting the points. (Clicking `Stop!`)
            • Getting a `bust` by rolling and not having any scoring dice. (This forfeits all points scored during this turn!)""", 
            inline=False
        )
        embed.add_field(
            name="Scoring", 
            value=f"""
            • a single {dice_emoji[1]} is worth 100 points;
            • a single {dice_emoji[5]} is worth 50 points;
            • three of a kind is worth 100 points multiplied by the given number, e.g. three {dice_emoji[4]} are worth 400 points;
            • three {dice_emoji[1]} are worth 1,000 points;
            • four or more of a kind is worth double the points of three of a kind, so four {dice_emoji[4]} are worth 800 points, five {dice_emoji[4]} are worth 1,600 points etc.
            • full straight {dice_emoji[1]}-{dice_emoji[6]} is worth 1500 points.
            • partial straight {dice_emoji[1]}-{dice_emoji[5]} is worth 500 points.
            • partial straight {dice_emoji[2]}-{dice_emoji[6]} is worth 750 points.""", 
            inline=False
        )
        await ctx.respond(embed=embed)
        

    @farkle.command(name="start", brief="start a game of Farkle")
    async def start_game(self, ctx, rival: discord.commands.Option(discord.User, "Player, you want to play with (anyone if not provided)", default=None), winning_score: discord.commands.Option(int, "Amount of point, at which a player will win the game (default is 4000)", min_value=50, default=4000)):
        """Starts a game of Farkle"""
        invitation = AcceptChallengeView(ctx, rival)
        if rival:
            await ctx.respond(f"{rival.mention}, {ctx.author.mention} has invited you to a game of Farkle to {winning_score} points! Click below to accept/deny the invitaion!", view=invitation)
        else:
            invitation.remove_item([button for button in invitation.children if button.style == discord.ButtonStyle.red][0])
            await ctx.respond(f"{ctx.author.mention} is looking for anyone, to play a game of Farkle to {winning_score} points with them! Click below to accept the invitaion!", view=invitation)
            
        invitation_timed_out = await invitation.wait()
        if invitation_timed_out or invitation.denied:
            return

        rival = invitation.rival
        scores = {0: 0, 1: 0}
        players = [ctx.author, rival]
        current_player = random.randint(0, 1)
        
        everyone_permissions = discord.PermissionOverwrite(send_messages=False, add_reactions=False)
        opponent_permissions = discord.PermissionOverwrite(send_messages=False, add_reactions=False)        
        player_permissions = discord.PermissionOverwrite(send_messages=True, add_reactions=False)
        
        current_game_channel = await ctx.guild.create_text_channel(
            name = f"farkle_◊_«{players[0].name}»_vs_«{players[1].name}»", 
            reason = f"{players[0].name} is playing Farkle with {players[1].name}",
            category = [category[0] for category in ctx.guild.by_category() if category[0] if category[0].id == db['guilds'][str(ctx.guild.id)]['games_category_id']][0]
        )
        await current_game_channel.set_permissions(
            target=ctx.guild.default_role, 
            overwrite=everyone_permissions
        )
        
        while True:
            await current_game_channel.set_permissions(
                target=players[(current_player+1)%2], 
                overwrite=opponent_permissions,
                reason="It's not their turn"
            )
            await current_game_channel.set_permissions(
                target=players[current_player], 
                overwrite=player_permissions, 
                reason="Now it's their turn"
            )
            dice_remaining = 6
            
            dice = dict()
            for die_id in range(dice_remaining):
                dice[die_id] = dice_emoji[random.randint(1, 6)]
            round_view = FarkleRoundView(ctx, dice, dice_remaining, 0, scores, players, current_player, winning_score)
            round_embed = round_view.round_embed()
            await current_game_channel.send(
                content=f"{players[current_player].mention}, it's your turn!",
                embed=round_embed, 
                view=round_view
            )
            timed_out = await round_view.wait()
            if not timed_out:
                scores[current_player] += round_view.round_score
            final_message = None
            
            if sorted([v for k, v in scores.items()])[-1] >= winning_score:    # if biggest score >= winning_score (someone won)
                # await ctx.send(f"**{players[current_player].mention} won!**")
                break
                
            elif timed_out:
                final_message = f"{players[current_player].mention} abandoned the game.\n**{players[(current_player+1)%2].mention} won by default!**"
                current_player = (current_player+1)%2
                break
                
            else:
                current_player = (current_player+1)%2
                continue

        await current_game_channel.delete(reason = "Game Ended")
        # final scores
        crown1 = ""
        crown2 = ""
        if current_player == 0:
            crown1 = ":crown:"
        else:
            crown2 = ":crown:"
        embed = discord.Embed(
            color = discord.Color.gold(),
            title = f"{players[current_player].name} won!",
            description = f"Final scores:\n{players[0].mention}{crown1} - `{scores[0]}`\n{players[1].mention}{crown2} - `{scores[1]}`"
        )
        await ctx.respond(content=final_message, embed=embed)
        
    
    print(f"** SUCCESSFULLY LOADED {__name__} **")


def setup(bot):
    bot.add_cog(Farkle(bot))
    # bot.add_application_command(farkle)
