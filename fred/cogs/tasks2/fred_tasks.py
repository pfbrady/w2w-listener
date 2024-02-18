from __future__ import annotations

import discord
from discord.ext import commands, tasks
import datetime
import pytz
import fred.w2w as w2w
import fred.cogs.cog_helper as ch
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from fred import Fred
    from whentowork import Position


from itertools import cycle

#status = cycle(['status 1', 'status 2', 'status 3'])

class Tasks(commands.Cog):
    def __init__(self, fred):
        self.fred: Fred = fred
        self.update_tables.start()
        self.send_vats_to_sups.start()
        self.check_pool_extreme_times.start()

    def cog_unload(self):
        self.update_tables.cancel()
        self.check_pool_extreme_times.cancel()

    @tasks.loop(minutes=30)
    async def update_tables(self):
        for branch in self.fred.ymca.branches.values():
            self.fred.ymca.database.update_rss(branch)
            for pool_group in branch.pool_groups:
                for pool in pool_group.pools:
                    if pool.is_open:
                        for channel in branch.guild.text_channels:
                            if channel.name == 'test3':
                                last_chem = self.fred.ymca.database.select_last_chem(branch, pool)
                                now = datetime.datetime.now()
                                positions: List[Position] = [branch.w2w_client.specialist, branch.w2w_client.supervisor, pool_group.w2w_lifeguard_position]
                                shifts = branch.w2w_client.get_shifts_now(positions)
                                w2w_employees = branch.w2w_client.unique_employees(shifts)        
                                discord_users = self.fred.ymca.database.select_discord_users(branch, w2w_employees)
                                if (last_chem
                                    and now > last_chem.sample_time + datetime.timedelta(hours=2, minutes=30)
                                    and now > pool.opening_time + datetime.timedelta(hours=2, minutes=30)
                                    and now < pool.closing_time - datetime.timedelta(minutes=30)
                                ):
                                    await channel.send(f"Notification: {' '.join([user.mention for user in discord_users])} Please submit a chemical check for the {pool.name}.")
                                last_opening = None
                                for checklist in pool.checklists:
                                    lo_candidate = self.fred.ymca.database.select_last_opening(branch, checklist)
                                    if lo_candidate:
                                        if not last_opening:
                                            last_opening = lo_candidate
                                        elif lo_candidate.opening_time < last_opening.opening_time:
                                            last_opening = lo_candidate
                                if (last_opening
                                    and now > last_opening.opening_time + datetime.timedelta(hours=16)
                                    and now > pool.opening_time + datetime.timedelta(hours=1, minutes=30)
                                    and now < pool.closing_time - datetime.timedelta(minutes=30)
                                ):
                                    await channel.send(f"Notification: {' '.join([user.mention for user in discord_users])} Please submit an opening checklist for the {pool.name}.")

    @update_tables.before_loop
    async def before_update_tables(self):
        print('Waiting for Fred to be ready before initializing update_tables task')
        await self.fred.wait_until_ready()

    @tasks.loop(time=datetime.time(hour=14, minute=9, tzinfo=pytz.timezone('US/Eastern')))
    async def send_vats_to_sups(self):
        now = datetime.datetime.now()
        if now.day == 14 or 28:
            for branch in self.fred.ymca.branches.values():         
                for channel in branch.guild.text_channels:
                    if channel.name == 'test3':
                        embed = discord.Embed(color=discord.Colour.from_str('#008080'), title=f"Summary of VATs (Guards, {now.strftime('%B %Y')})", description=ch.vat_sup_dashboard(branch, now))
                        await channel.send(embed=embed)

    @tasks.loop(time=datetime.time(hour=0, minute=15, tzinfo=pytz.timezone('US/Eastern')))
    async def check_pool_extreme_times(self):
        for branch in self.fred.ymca.branches.values():
            branch.update_pools()
            for guild in self.fred.guilds:
                    for channel in guild.text_channels:
                        if channel.name == 'test3':
                            await channel.send(f"Updating opening/closing times for each pool at {branch.name} Branch.")

async def setup(fred: Fred):
    await fred.add_cog(Tasks(fred))