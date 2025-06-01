import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import os, random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.synced = False

bot = MyBot()

infection_roles = [
    "Survivor",
    "Infected I",
    "Infected II",
    "Infected III",
    "Hive Master"
]

infection_stage = {}  # user_id: stage (0-4)
infected_users = set()

infection_flavor = [
    "🧊 A chill runs through you. Something is wrong...",
    "💀 You hear whispers. Your hands tremble.",
    "🩸 Your skin crawls. You're not alone in your mind.",
    "🧠 You are no longer you. The Hive is all. Obey."
]

visibility_shrink = [0.0, 0.1, 0.3, 0.5, 0.99]

async def advance_infection(member: discord.Member):
    uid = member.id
    current_stage = infection_stage.get(uid, 0)
    if current_stage >= 4:
        return

    new_stage = current_stage + 1
    infection_stage[uid] = new_stage
    infected_users.add(uid)

    old_role = discord.utils.get(member.guild.roles, name=infection_roles[current_stage])
    if old_role:
        await member.remove_roles(old_role)
    new_role = discord.utils.get(member.guild.roles, name=infection_roles[new_stage])
    if new_role:
        await member.add_roles(new_role)

    try:
        await member.send(infection_flavor[new_stage - 1])
    except:
        pass

    await update_channel_visibility(member, new_stage)

async def update_channel_visibility(member: discord.Member, stage: int):
    text_channels = [c for c in member.guild.channels if isinstance(c, discord.TextChannel)]
    hide_count = int(len(text_channels) * visibility_shrink[stage])
    to_hide = random.sample(text_channels, hide_count)
    for channel in to_hide:
        try:
            await channel.set_permissions(member, read_messages=False)
        except:
            pass

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    await create_roles()
    infection_loop.start()
    if not bot.synced:
        await bot.tree.sync()
        bot.synced = True

async def create_roles():
    for guild in bot.guilds:
        for role_name in infection_roles:
            if not discord.utils.get(guild.roles, name=role_name):
                await guild.create_role(name=role_name)
                print(f"Created role: {role_name}")

@bot.command()
async def status(ctx):
    uid = ctx.author.id
    stage = infection_stage.get(uid, 0)
    role = infection_roles[stage]
    await ctx.send(f"> 🧬 {ctx.author.mention}, your current status: **{role}**")

@bot.command()
async def infect(ctx, member: discord.Member):
    if member.bot:
        return
    if infection_stage.get(member.id, 0) > 0:
        return await ctx.send(f"⚠️ {member.display_name} is already infected.")
    await advance_infection(member)
    await ctx.send(f"☣️ {member.display_name} has been infected!")

@bot.tree.command(name="status")
async def slash_status(interaction: discord.Interaction):
    uid = interaction.user.id
    stage = infection_stage.get(uid, 0)
    role = infection_roles[stage]
    await interaction.response.send_message(f"> 🧬 {interaction.user.mention}, your current status: **{role}**", ephemeral=True)

@bot.tree.command(name="infect")
@app_commands.describe(member="The user to infect")
async def slash_infect(interaction: discord.Interaction, member: discord.Member):
    if member.bot:
        return await interaction.response.send_message("❌ Can't infect a bot!", ephemeral=True)
    if infection_stage.get(member.id, 0) > 0:
        return await interaction.response.send_message(f"{member.display_name} is already infected.", ephemeral=True)
    await advance_infection(member)
    await interaction.response.send_message(f"☣️ {member.display_name} has been infected!")

@tasks.loop(minutes=10)
async def infection_loop():
    for guild in bot.guilds:
        survivors = [m for m in guild.members if not m.bot and infection_stage.get(m.id, 0) == 0]
        if survivors and random.random() < 0.3:
            victim = random.choice(survivors)
            await advance_infection(victim)
            try:
                await victim.send("🦠 You feel strange... something is changing inside you.")
            except:
                pass

bot.run(TOKEN)
