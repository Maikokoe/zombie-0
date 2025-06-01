import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os, random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

infection_roles = [
    "Survivor",
    "Infected I",
    "Infected II",
    "Infected III",
    "Hive Master"
]

infected_users = set()
infection_stage = {}  # user_id: stage (0-4)

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    infection_loop.start()

@bot.command()
async def status(ctx):
    uid = ctx.author.id
    stage = infection_stage.get(uid, 0)
    await ctx.send(f"{ctx.author.mention}, current status: **{infection_roles[stage]}**")

@bot.command()
async def infect(ctx, member: discord.Member):
    if member.bot:
        return
    uid = member.id
    if uid in infection_stage:
        await ctx.send(f"{member.display_name} is already infected!")
        return

    infection_stage[uid] = 1
    infected_users.add(uid)
    role = discord.utils.get(ctx.guild.roles, name="Infected I")
    if role:
        await member.add_roles(role)
    await member.send("🧟 You feel cold... You are now **Infected I**.\nSpeak carefully...")
    await ctx.send(f"{member.mention} has been infected!")

@bot.command()
async def duel(ctx, member: discord.Member):
    await ctx.send(f"{ctx.author.mention} challenges {member.mention} to an infection duel! (⚔️ Placeholder for turn-based battle logic)")

@bot.command()
async def cure(ctx):
    uid = ctx.author.id
    if uid in infection_stage and infection_stage[uid] > 0:
        if random.random() > 0.5:
            infection_stage[uid] = 0
            infected_users.discard(uid)
            await ctx.send(f"💉 {ctx.author.mention} has been **cured**!")
        else:
            await ctx.send(f"⚠️ Fake cure! {ctx.author.mention}'s infection advances...")
            infection_stage[uid] = min(4, infection_stage[uid] + 1)
    else:
        await ctx.send("You're not infected.")

@tasks.loop(minutes=10)
async def infection_loop():
    for guild in bot.guilds:
        members = [m for m in guild.members if not m.bot]
        survivors = [m for m in members if infection_stage.get(m.id, 0) == 0]
        if survivors and random.random() < 0.3:  # 30% chance to infect a random survivor
            victim = random.choice(survivors)
            infection_stage[victim.id] = 1
            infected_users.add(victim.id)
            role = discord.utils.get(guild.roles, name="Infected I")
            if role:
                await victim.add_roles(role)
            try:
                await victim.send("🧟 You feel dizzy... You are now **Infected I**.")
            except:
                pass

bot.run(TOKEN)
