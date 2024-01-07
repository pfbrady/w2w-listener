import datetime
import typing
import discord
from discord.ext import commands, tasks
import w2w

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Fred

class W2W_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred
        self.guards_default_times = ['now', 'earlier-today', 'later-today', 'today', 'today-closers', 'tomorrow', 'tomorrow-openers', 'tomorrow-closers', 'week', 'week-openers', 'week-closers']
        self.guards_default_pos = ['all', 'complex', 'main']
        self.instructors_default_times = ['earlier-today', 'later-today', 'today', 'tomorrow', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        self.instructors_default_pos = ['all', 'group', 'privates', 'swam']

    @discord.app_commands.command()
    async def testy(self, interaction:discord.Interaction):
        self.fred.database.update_tables_rss()
        await interaction.response.send_message(f'hrloo')

    async def guards_time_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.guards_default_times if current.lower() in default_time.lower()
        ]
    
    async def guards_pos_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in self.guards_default_pos if current.lower() in default_pos.lower()
        ]
    

    @discord.app_commands.command(description="guards")
    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=guards_time_auto, position=guards_pos_auto)
    async def guards2(self, interaction:discord.Interaction, time: str, position: str, message: str):
        w2w_pos = w2w.w2wpos_from_default_pos(position, w2w.W2WPosition.GUARDS)
        w2w_users = w2w.w2w_from_default_time(time, w2w_pos)
        employees = self.fred.database.select_discord_users(w2w_users)
        employees_formatted = [f'<@{id}>' for id in employees]
        await interaction.response.send_message(f"Notification: {' '.join(employees_formatted)}: {message}")
  
    async def instructors_time_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.instructors_default_times if current.lower() in default_time.lower()
        ]
    
    async def instructors_pos_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in self.instructors_default_pos if current.lower() in default_pos.lower()
        ]

    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=instructors_time_auto, position=instructors_pos_auto) 
    @discord.app_commands.command(description="instructors")
    async def instructors(self, interaction:discord.Interaction, time: str, position: str, message: str):
        w2w_pos = w2w.w2wpos_from_default_pos(position, w2w.W2WPosition.INSTRUCTORS)
        w2w_users = w2w.w2w_from_default_time(time, w2w_pos)
        employees = self.fred.database.select_discord_users(w2w_users)
        employees_formatted = [f'<@{id}>' for id in employees]
        await interaction.response.send_message(f"__Notification__: {' '.join(employees_formatted)}: {message}.", ephemeral=True)

async def setup(fred):
    fred.tree.add_command(W2W_Commands(name="w2w", description="test", fred=fred))