from decouple import config

import discord
from discord.ext import commands
from tabulate import tabulate

from ivi import calculate_ivi_score

TOKEN = config('DISCORD_TOKEN')

SERVICE_ID = config('SERVICE_ID', default='example')

bot = commands.Bot(command_prefix='!')


@bot.command(name='ivi')
async def get_ivi(ctx, username: str):
    data = calculate_ivi_score(username, service_id=SERVICE_ID)

    embed = discord.Embed(title=data['Playername'])

    embed.add_field(name='Kills since:', value=data['kills_since'].strftime('%Y-%m-%d %H:%M'), inline=True)
    if data['accuracy_since'] is not None:
        embed.add_field(name='Accuracy data since:', value=data['accuracy_since'].strftime('%Y-%m-%d'), inline=True)
    else:
        embed.add_field(name='Accuracy data since:', value="forever", inline=True)

    recent_data_table = []

    for playerclass, stats in data['timeframe_stats'].items():
        recent_data_table.append(
            [playerclass, round(stats['ivi'], 3), round(stats['accuracy'], 3), round(stats['hsr'], 3),
             stats['headshots'], stats['kills']])

    timeframe_table = '```' + tabulate(recent_data_table, headers=["Class", 'IvI', 'ACC', "HSR", "HS", "Kills"]) + '```'

    embed.add_field(name=f"{data['timeframe'].capitalize()} IvI", value=round(data['timeframe_ivi'], 4), inline=False)

    embed.add_field(name="IvI by class", value=timeframe_table, inline=False)

    if data['timeframe'] != 'forever':

        forever_data_table = []

        for playerclass, stats in data['forever_stats'].items():
            forever_data_table.append(
                [playerclass, round(stats['ivi'], 3), round(stats['accuracy'], 3), round(stats['hsr'], 3),
                 stats['headshots'], stats['kills']])

        forever_table = '```' + tabulate(forever_data_table,
                                         headers=["Class", 'IvI', 'ACC', "HSR", "HS", "Kills"]) + '```'

        embed.add_field(name='\u200b', value='\u200b', inline=False)

        embed.add_field(name="Overall forever accuracy IvI:", value=round(data['forever_ivi'], 4), inline=False)

        embed.add_field(name="IvI using all-time accuracy data", value=forever_table, inline=False)

    await ctx.send(embed=embed)
    return


bot.run(TOKEN)
