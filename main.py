import os
import nextcord
from nextcord.ext import commands
from config import DISCORD_BOT_TOKEN, CHANNEL_ID
from utils.logger import logger

# Create necessary directories
os.makedirs('generated_images', exist_ok=True)

# Bot setup
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs
try:
    bot.load_extension('cogs.image_generation')
    logger.info("Successfully loaded image_generation cog")
except Exception as e:
    logger.error(f"Failed to load image_generation cog: {str(e)}")

@bot.event
async def on_ready():
    logger.info(f'Bot is ready. Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Bot is in {len(bot.guilds)} guild(s)')
    for guild in bot.guilds:
        logger.info(f' - {guild.name} (ID: {guild.id})')
    
    # Send online message
    channel = bot.get_channel(int(CHANNEL_ID))
    if channel:
        user_id = 277656871987576833
        try:
            await channel.send(f"<@{user_id}> online")
            logger.info(f"Sent online message in channel {CHANNEL_ID}")
        except nextcord.errors.Forbidden:
            logger.error(f"Bot doesn't have permission to send messages in channel {CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Failed to send online message: {str(e)}")
    else:
        logger.error(f"Failed to find channel with ID: {CHANNEL_ID}")

@bot.event
async def on_message(message):
    if message.channel.id != int(CHANNEL_ID):
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    logger.info("Main script started")
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start the bot: {str(e)}")