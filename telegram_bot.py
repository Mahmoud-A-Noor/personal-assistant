import asyncio
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("nest_asyncio not installed. Installing now...")
    import subprocess
    subprocess.run(["pip", "install", "nest_asyncio"])
    print("nest_asyncio installed. Please rerun the script.")
    exit(1)

from tools.telegram import TelegramBot

def main():
    """Main function to initialize and run the bot."""
    bot = TelegramBot()
    return bot.run()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())