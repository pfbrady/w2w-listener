import settings
from discord.ext.commands import Bot
import logging
import asyncio
import cogs.tasks2.fred_tasks
import cogs.commands2.supervisor.w2w_get_commands as w2w_get
import database as db
import ymca as y


class Fred(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = None
        self.ymca = None

    async def setup_hook(self) -> None:
        self.ymca = y.YMCA('YMCA of Delaware')
        self.database = db.YMCADatabase()

    async def on_ready(self):
        for guild in self.guilds:
            for branch_id, branch_info in settings.SETTINGS_DICT['branches'].items():
                if branch_info['guild_id'] == guild.id:
                    self.database.init_discord_users(self.get_all_members(), branch_id)
                    self.database.init_w2w_users(branch_id)
        #self.database.load_chems()
        #self.database.load_vats()
 
        await self.load_extension("cogs.commands2.supervisor.w2w_commands")
        await self.load_extension("cogs.commands2.supervisor.formstack_commands")
        await self.load_extension("cogs.tasks2.fred_tasks")
        self.tree.copy_global_to(guild=self.guilds[0])
        await self.tree.sync(guild=self.guilds[0])

        await w2w_get.setup(self)
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
