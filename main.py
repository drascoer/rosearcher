import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Constants
ROBLOX_API_BASE = "https://users.roblox.com/v1"
ROBLOX_HEADSHOT_API = "https://www.roblox.com/headshot-thumbnail/image"

class RobloxSearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rsearch", description="Search for a Roblox user")
    @app_commands.describe(username="The Roblox username to search for")
    async def roblox_search(self, interaction: discord.Interaction, username: str):
        """Search for a Roblox user and display their profile information"""
        
        # Defer the response as API calls might take time
        await interaction.response.defer()
        
        try:
            # Validate input
            if not username or len(username.strip()) == 0:
                embed = discord.Embed(
                    title="❌ Invalid Input",
                    description="Please provide a valid username.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            if len(username) > 20:
                embed = discord.Embed(
                    title="❌ Username Too Long",
                    description="Roblox usernames cannot exceed 20 characters.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            # Search for the user using the new API endpoint
            search_response = requests.get(
                f"{ROBLOX_API_BASE}/users/search",
                params={"keyword": username, "limit": 1},
                timeout=5
            )
            search_response.raise_for_status()
            search_data = search_response.json()

            if not search_data.get("data") or len(search_data["data"]) == 0:
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description=f"No Roblox user found with username: `{username}`",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            user_search = search_data["data"][0]
            user_id = user_search["id"]

            # Get detailed user information
            user_response = requests.get(
                f"{ROBLOX_API_BASE}/users/{user_id}",
                timeout=5
            )
            user_response.raise_for_status()
            user_info = user_response.json()

            # Get user friends count
            friends_response = requests.get(
                f"{ROBLOX_API_BASE}/users/{user_id}/friends/count",
                timeout=5
            )
            friends_count = friends_response.json().get("count", "N/A") if friends_response.ok else "N/A"

            # Get user followers count
            followers_response = requests.get(
                f"{ROBLOX_API_BASE}/users/{user_id}/followers/count",
                timeout=5
            )
            followers_count = followers_response.json().get("count", "N/A") if followers_response.ok else "N/A"

            # Parse account creation date
            created_date = datetime.fromisoformat(user_info["created"].replace("Z", "+00:00"))
            account_age = (datetime.now(created_date.tzinfo) - created_date).days

            # Create the embed
            embed = discord.Embed(
                title=f"🎮 {user_info['displayName']}",
                description=user_info.get("description", "*No bio set*") or "*No bio set*",
                color=discord.Color.blurple(),
                url=f"https://www.roblox.com/users/{user_id}/profile"
            )

            # Add fields
            embed.add_field(
                name="👤 Username",
                value=f"`{user_info['name']}`",
                inline=True
            )
            embed.add_field(
                name="🆔 User ID",
                value=f"`{user_id}`",
                inline=True
            )
            embed.add_field(
                name="📅 Account Created",
                value=f"`{created_date.strftime('%B %d, %Y')}`",
                inline=True
            )
            embed.add_field(
                name="⏳ Account Age",
                value=f"`{account_age} days`",
                inline=True
            )
            embed.add_field(
                name="👥 Friends",
                value=f"`{friends_count}`",
                inline=True
            )
            embed.add_field(
                name="⭐ Followers",
                value=f"`{followers_count}`",
                inline=True
            )

            # Check if banned
            if user_info.get("isBanned", False):
                embed.add_field(
                    name="⚠️ Status",
                    value="🔒 **BANNED**",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Status",
                    value="Active",
                    inline=False
                )

            # Set thumbnail
            thumbnail_url = f"{ROBLOX_HEADSHOT_API}?userId={user_id}&width=420&height=420&format=png"
            embed.set_thumbnail(url=thumbnail_url)

            # Set footer
            embed.set_footer(
                text=f"Requested by {interaction.user}",
                icon_url=interaction.user.display_avatar.url
            )

            await interaction.followup.send(embed=embed)

        except requests.exceptions.Timeout:
            embed = discord.Embed(
                title="❌ Request Timeout",
                description="The Roblox API took too long to respond. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

        except requests.exceptions.RequestException as e:
            embed = discord.Embed(
                title="❌ API Error",
                description=f"Error connecting to Roblox API: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

async def main():
    """Start the bot"""
    await bot.add_cog(RobloxSearchCog(bot))
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ Error: DISCORD_TOKEN not found in .env file")
        return
    
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
