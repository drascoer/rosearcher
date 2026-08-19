import discord
from discord.ext import commands
from discord import app_commands
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get token from environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Bot is ready"""
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@bot.tree.command(name="rsearch", description="Search for a Roblox user")
@app_commands.describe(username="The Roblox username to search for")
async def rsearch(interaction: discord.Interaction, username: str):
    """Search for a Roblox user"""
    await interaction.response.defer()
    
    try:
        # Validate input
        if not username or len(username.strip()) == 0:
            await interaction.followup.send("❌ Please provide a username!")
            return

        # Search for user
        response = requests.get(
            "https://users.roblox.com/v1/users/search",
            params={"keyword": username, "limit": 1},
            timeout=5
        )
        data = response.json()

        # Check if user found
        if not data.get("data") or len(data["data"]) == 0:
            await interaction.followup.send(f"❌ User '{username}' not found!")
            return

        user = data["data"][0]
        user_id = user["id"]

        # Get full user info
        user_info = requests.get(f"https://users.roblox.com/v1/users/{user_id}", timeout=5).json()

        # Get friends count
        friends = requests.get(f"https://users.roblox.com/v1/users/{user_id}/friends/count", timeout=5).json()
        friends_count = friends.get("count", "N/A")

        # Get followers count
        followers = requests.get(f"https://users.roblox.com/v1/users/{user_id}/followers/count", timeout=5).json()
        followers_count = followers.get("count", "N/A")

        # Create embed
        embed = discord.Embed(
            title=f"🎮 {user_info['displayName']}",
            description=user_info.get("description") or "No bio set",
            color=discord.Color.blurple(),
            url=f"https://www.roblox.com/users/{user_id}/profile"
        )

        embed.add_field(name="Username", value=f"`{user_info['name']}`", inline=True)
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
        embed.add_field(name="Friends", value=f"`{friends_count}`", inline=True)
        embed.add_field(name="Followers", value=f"`{followers_count}`", inline=True)

        if user_info.get("isBanned"):
            embed.add_field(name="Status", value="🔒 BANNED", inline=False)
        else:
            embed.add_field(name="Status", value="✅ Active", inline=False)

        # Set avatar
        embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png")
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    except requests.exceptions.Timeout:
        await interaction.followup.send("❌ Request timed out. Try again!")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# Start bot with error checking
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found!")
        print("Make sure your .env file contains: DISCORD_TOKEN=your_token_here")
    else:
        print("✅ Token loaded successfully!")
        bot.run(DISCORD_TOKEN)
