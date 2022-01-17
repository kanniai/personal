# Discord bot
# Author: kanniai

import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
import numpy as np
import os


TOKEN = 'OTAwNzMxMjk2OTI0NDM0NDUy.YXFlYw.BVjx8rFtQxpStDJ_aQjZkqj3fXI'
COMMAND_PREFIX = '%'

bot = commands.Bot(command_prefix=COMMAND_PREFIX)


@bot.event
async def on_ready():
    print("Connected...")


@bot.command()
async def context(ctx):
    await on_message(ctx)


@bot.event
async def on_message(message):
    ### Read the messages on the channel ###

    commands = get_bot_commands()
    if message.content == commands[0]:
        await results(message)
    elif message.content == commands[1]:
        await print_help(message)
    elif message.content == commands[2]:
        await delete(message)
    elif message.content in commands[3]:
        await individual_scores(message, commands[3].index(message.content))
    elif message.content[0] == COMMAND_PREFIX:
        await error_message(message)
    if message.author == bot.user:
        return


async def individual_scores(message, idx):
    ### Consider only one person's message history ###

    count, points, highest, highest_id = [0 for _ in range(4)]
    points_array = []
    async for msg in message.channel.history(limit=100000):
        # Only consider messages from the given author
        if msg.author.id != get_author_ids()[idx][0]:
            continue
        # Check if photo or a video-link
        if len(msg.attachments) > 0 or 'https' in msg.content:
            count += 1
            temp_points = reaction_emojis(msg.reactions)
            highest, highest_id = top_score(temp_points, highest, msg.id, highest_id)
            points += temp_points
            points_array.append(round_nearest(temp_points, 1/3))

    # Send a message of the user info to the channel
    msg = user_info([count, convert_to_letters(points, count), convert_to_letters(highest, 1), highest_id], idx)
    await message.channel.send(msg)

    plot_individual(points_array, idx)

    await message.channel.send(file=discord.File('individual.png'))
    os.remove('individual.png')
    await bot.process_commands(message)


async def print_help(message):
    ### Send a information message about the bot to the channel ###

    help_msg = "I'm just a simple bot, but I'll do what I can.\n\n" \
               "To use me, type one of the following commands:\n" \
               " %help: open this window\n" \
               " %results: overview of the meme statistics\n" \
               " %delete: delete all messages sent by this bot (not to flood the channel)\n" \
               " %<name>: individual statistics\n" \
               "   - Select name: [matias, antti, mikke, eetu, niklas, aatu j, aatu w, eemil, masa]\n" \
               "     - Example input: %matias"
    await message.channel.send(help_msg)


async def results(message):
    ### Produce the overall results of the messages of the channel ###

    # Initialize the data grid
    authors = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
    async for msg in message.channel.history(limit=100000):
        # Check if photo or a video-link
        if len(msg.attachments) > 0 or 'https' in msg.content:
            authors = check_message(msg, authors)

    # Feed the data to plotting function
    bar_plot(list([authors[i][0], convert_to_letters(authors[i][1], authors[i][0])] for i in range(0, 9)))

    # Send the plot to the channel
    await message.channel.send(file=discord.File('results.png'))
    os.remove('results.png')
    await bot.process_commands(message)


async def delete(message):
    ### Delete all messages sent by bot and the commands sent by users

    async for msg in message.channel.history(limit=100000):
        # Only consider messages from the bot
        if msg.author.id == get_bot_id():
            await msg.delete()
        # Delete also the commands sent by user
        elif msg.content[0] == COMMAND_PREFIX:
            await msg.delete()


async def error_message(message):
    ### Send an error message to the channel if the input command is wrong ###

    msg = "Wrong command! Type %help to see the available commands."
    await message.channel.send(msg)


def get_bot_id():
    ### Return the bot id ###

    return 900731296924434452


def get_bot_commands():
    ### Return the available commands for the bot ###

    return ["%results", "%help", "%delete",
           ["%matias", "%antti", "%eetu", "%mikke", "%niklas", "%aatu j", "%aatu w", "%eemil", "%masa"]]


def top_score(points, highest, msg_id, highest_msg_id):
    ### Check if the new score is higher than the older high score ###

    if highest < points:
        return points, msg_id
    else: return highest, highest_msg_id


def get_author_ids():
    ### Return the id's of the channel authors ###

    return [[393481776493756416, "Matias"], [241512884180353024, "Antti"], [278483684934418433, "Eetu"],
            [244540194802368522, "Mikke"], [305051893883731970, "Niklas"], [395638082088468520, "Aatu J"],
            [568553294679638087, "Aatu W"], [202454171713011712, "Eemil"], [198884503022731266, "Masa"]]


def check_message(msg, authors):
    ### Check who sent the message, and save the data for that person ###

    author_ids = np.array(get_author_ids())[:, 0]
    author_ids = list(map(int, author_ids))
    # The bot id
    if msg.author.id == get_bot_id(): return authors
    if reaction_emojis(msg.reactions) == 0: return authors

    # Add count and points to the data grid
    authors[author_ids.index(msg.author.id)][0] += 1
    authors[author_ids.index(msg.author.id)][1] += reaction_emojis(msg.reactions)
    return authors


def reaction_emojis(reactions):
    ### Count the reactions of the given message and calculate the points based on the reactions ###

    points, count = 0, 0
    if len(reactions) == 0: return 0
    # Emoji ID's from discord
    emojis = {"<:Stier:896841079884759080>": 5, "<:atier:896841094896185354>": 4, "<:btier:896841105625214986>": 3,
              "<:ctier:896841116752683019>": 2, "<:dtier:896841129562091520>": 1}

    for reaction in reactions:
        # Only specific reactions
        if str(reaction) not in list(emojis.keys()): continue
        for _ in range(reaction.count):
            points += emojis[str(reaction)]
            count += 1
    return points / count


def convert_to_letters(grades, count):
    ### Convert the numerical values to letter grades ###

    points = float(round_nearest(grades / count, 0.33))
    # Get the corresponding scores
    reference_scores = np.arange(1, 16/3, 1/3, dtype=float)
    reference_scores = [round_nearest(x, 0.33) for x in reference_scores]

    converted_grades = get_grades()

    return converted_grades[list(reference_scores).index(points)]


def round_nearest(x, y):
    ### Round a given value x to another nearest given value y ###

    return round(x / y) * y


def color_bars(data, grades, colors):
    ### Return the color of the produced bar given the score ###

    idx = grades.index(data)
    return colors[idx]


def user_info(data, index):
    ### Print the info of the meme with the highest score of the given author ###

    msg = "User "+str(get_author_ids()[index][1])+" has sent "+str(data[0])+" memes to the channel " \
          "with an average of "+str(data[1])+". \n\n"+ \
          str(get_author_ids()[index][1])+"'s best meme is of tier "+str(data[2])+". The link to the meme:\n" \
          "https://discordapp.com/channels/540528274540068864/550688931310731274/"+str(data[3])
    return msg


def get_grades():
    ### Return the alphabetical grades corresponding to the numerical values ###

    return ["D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+", "S-", "S"]


def bar_plot(data):
    ### Produce a bar plot of the overview to be posted on the channel ###

    fig = plt.figure(figsize=(15, 6))
    gs = GridSpec(8, 9)

    count = np.array(data)[:, 0].astype(int)
    scores = np.array(data)[:, 1]
    bars = np.array(get_author_ids())[:,1]

    # Sort the bars based on the count number
    scores = [x for _, x in sorted(zip(count, scores), reverse=True)]
    bars = [y for _, y in sorted(zip(count, bars), reverse=True)]
    count = sorted(count, reverse=True)

    colors = ['royalblue', 'cyan', 'aquamarine', 'lime', 'lightgreen', 'greenyellow', 'yellow', 'gold',
              'orange', 'sandybrown', 'lightsalmon', 'salmon', 'red']

    # Custom colorbar representing the colors
    ax = fig.add_subplot(gs[7, 0:9])
    norm = mpl.colors.Normalize(vmin=1, vmax=14)
    cmap = mpl.colors.ListedColormap(colors)
    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal', extend='both')
    cb1.set_ticks([1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5])
    cb1.set_ticklabels(get_grades())
    cb1.set_label("Tiers")

    # Determine the colors of the bars
    c = []
    for score in scores:
        c.append(color_bars(score, get_grades(), colors))
    ax2 = fig.add_subplot(gs[0:6, 0:9])
    barplot = plt.bar(bars, count, color=c)

    def text_labels():
        ### Nested function to produce text labels for the bar plot ###

        for idx, rect in enumerate(barplot):
            height = rect.get_height()
            ax2.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                     'N=' + str(count[idx]) + '\n' + str(scores[idx]),
                     ha='center', va='bottom', rotation=0)

    text_labels()
    ax2.set_ylim(0, int(max(count)) + 10)
    ax2.set_ylabel("Count of the memes")
    plt.title("Average of the memes")
    plt.xticks(bars)
    plt.savefig('results.png')
    return


def plot_individual(data, index):
    ### Plot the individual performance ###

    # Change the direction of the data to go from left to right
    data.reverse()

    ax = plt.figure(figsize=(15, 6)).gca()
    n = np.arange(1, len(data)+1)
    plt.plot(n, data, linestyle='-', marker='o', color='black')

    ax.set_xlabel("Memes")
    ax.set_ylabel("Tier")
    # Custom y-labels
    plt.yticks(np.arange(1, 16/3, 1/3), get_grades())
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.title("Meme scores of "+str(get_author_ids()[index][1]))
    plt.savefig('individual.png')
    return


bot.run(TOKEN)
