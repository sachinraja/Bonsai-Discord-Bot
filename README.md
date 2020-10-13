<h1>
  <img src="https://i.imgur.com/SX7Yfdf.png" alt="Avatar" width="50" height="50">
  Bonsai-Discord-Bot
</h1>

Customize three different bonsai trees using parts (base, trunk, and leaves) from the marketplace and setting a background color. All users can upload these parts thier shop and earn money when someone buys from them. Those customers can then replace the parts in their trees with the ones in their inventories whenever they like. There is, however, a max of 15 parts in each user's shop.

[![Support Server](https://img.shields.io/discord/753416400319545374?logo=discord&style=for-the-badge)](https://discord.gg/tNC22WD)
![Stars](https://img.shields.io/github/stars/xCloudzx/Bonsai-Discord-Bot?style=for-the-badge)
[![MIT License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](https://github.com/xCloudzx/Bonsai-Discord-Bot/blob/master/LICENSE)

## Links
[Add Bot to Server](https://discord.com/api/oauth2/authorize?client_id=743898864926589029&permissions=8192&scope=bot)

## Usage
  * The default command prefix for the bot is `b!`, but you can change this with the `prefix` command.
  * Use the `help` command for more info on the commands.


## Self-Hosting
Running your own instance of this bot is not recommended, it is more preferable that you invite it to your server. No support for self-hosting will be provided.

1. Clone the repository for this bot: `git clone https://github.com/xCloudzx/Bonsai-Discord-Bot.git`.
2. Install required packages: `pip install -r requirements.txt`.
3. Create a MongoDB database. You can either use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) or [download a database](https://www.mongodb.com/try/download/community).
4. Open the folder and create a .env file. Enter:
    ```
    TOKEN = Discord bot # Go to https://discord.com/developers/applications/ and click on your bot to get it.
    MONGODB_URI = Connection to MongoDB database # Format: mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]].
    ```
    Go [here](https://docs.mongodb.com/manual/reference/connection-string) for more information on your connection string for `MONGODB_URI`.
5. Run the bot: `python bot.py`.