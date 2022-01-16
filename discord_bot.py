# Discord bot
# Author: kanniai

import os
from discord.ext import commands
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.gridspec import GridSpec
import discord
import numpy as np

# Connect the bot
TOKEN = 'OTAwNzMxMjk2OTI0NDM0NDUy.YXFlYw.OCTC9RlNsIQlIVoWh6TI1JRhHfs'

bot = commands.Bot(command_prefix="%")


@bot.event
async def on_ready():
    print("Connected...")


@bot.command()
async def context(ctx):
    await on_message(ctx)


@bot.event
async def on_message(message):
    ### Read the messages on the channel ###
    names = ["%matias", "%antti", "%eetu", "%mikke", "%niklas", "%aatu j", "%aatu w", "%eemil", "%masa"]

    if message.content == "%results":
        await results(message)
    elif message.content == "%help":
        await print_help(message)
    elif message.content in names:
        await individual_scores(message, names.index(message.content))
    else: return
    if message.author == bot.user:
        return


async def individual_scores(message, idx):
    ### Consider only one person's message history ###

    count, points, highest, highest_id = [0 for _ in range(4)]
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

    # Send a message of the user info to the channel
    msg = user_info([count, convert_to_letters(points, count), convert_to_letters(highest, 1), highest_id], idx)
    await message.channel.send(msg)

    #plot_individual([count, convert_to_letters(points, count)], idx)


async def print_help(message):
    ### Send a information message about the bot to the channel ###

    help_msg = "I'm just a simple bot, but I'll do what I can.\n\n" \
               "To use me, type one of the following commands:\n" \
               " %help: open this window\n" \
               " %results: overview of the meme statistics\n"
    await message.channel.send(help_msg)


async def results(message):
    ### Produce the overall results of the messages of the channel ###

    # Initialize the data grid
    # Matias, Antti, Eetu, Mikke, Niklas, Aatu J, Aatu W, Eemil,  Masa
    print(message)
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

    author_ids = get_author_ids()[:,0]
    # The bot id
    if msg.author.id == 900731296924434452: return authors
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
        # Only 'tier' reactions
        if str(reaction) not in list(emojis.keys()): continue
        for _ in range(reaction.count):
            points += emojis[str(reaction)]
            count += 1
    return points / count


def convert_to_letters(grades, count):
    ### Convert the numerical values to letter grades ###

    points = float(grades / count)
    if 1 <= points <= 1.25: return "D"
    elif 1.25 < points <= 1.5: return "D+"
    elif 1.5 < points <= 1.75: return "C-"
    elif 1.75 < points <= 2.25: return "C"
    elif 2.25 < points <= 2.5: return "C+"
    elif 2.5 < points <= 2.75: return "B-"
    elif 2.75 < points <= 3.25: return "B"
    elif 3.25 < points <= 3.5: return "B+"
    elif 3.5 < points <= 3.75: return "A-"
    elif 3.75 < points <= 4.25: return "A"
    elif 4.25 < points <= 4.5: return "A+"
    elif 4.5 < points <= 4.75: return "S-"
    elif 4.75 < points: return "S"


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


def bar_plot(data):
    ### Produce a bar plot of the overview to be posted on the channel ###

    fig = plt.figure(figsize=(15, 6))
    gs = GridSpec(8, 9)

    count = np.array(data)[:, 0].astype(int)
    scores = np.array(data)[:, 1]
    bars = ["Matias", "Antti", "Eetu", "Mikke", "Niklas", "Aatu J", "Aatu W", "Eemil", "Masa"]

    # Sort the bars based on the count number
    scores = [x for _, x in sorted(zip(count, scores), reverse=True)]
    bars = [y for _, y in sorted(zip(count, bars), reverse=True)]
    count = sorted(count, reverse=True)

    grades = ["D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+", "S-", "S"]
    colors = ['royalblue', 'cyan', 'aquamarine', 'lime', 'lightgreen', 'greenyellow', 'yellow', 'gold',
              'orange', 'sandybrown', 'lightsalmon', 'salmon', 'red']

    # Custom colorbar representing the colors
    ax = fig.add_subplot(gs[7, 0:9])
    norm = mpl.colors.Normalize(vmin=1, vmax=14)
    cmap = mpl.colors.ListedColormap(colors)
    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal', extend='both')
    cb1.set_ticks([1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5])
    cb1.set_ticklabels(grades)
    cb1.set_label("Grades")

    # Determine the colors of the bars
    c = []
    for score in scores:
        c.append(color_bars(score, grades, colors))
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

    fig = plt.figure(figsize=(15, 6))


bot.run(TOKEN)
