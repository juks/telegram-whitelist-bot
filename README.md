# What is it?
<img width="723" height="439" alt="image" src="https://github.com/user-attachments/assets/4a16ff48-17a4-4235-8ef3-a8ba1fb1f0a6" />

Simple bot that adds whitelist automation to Telegram chats. Those users requests who is listed in chat whitelist will be accepted automatically.

## Installation and running

* Install Docker Engine;
* Clone the repository;
* Copy .env.dist to .env and update your configuration;
* Execute _docker compose run --remove-orphans --build telegram-whitelist-bot_.

## How to use the bot
* Add bot to your Telegram chat;
* Grant admin permissions to the bot;
* Set the whilelist location.
* Create moderated invitation link.

<img width="350" alt="image" src="https://github.com/user-attachments/assets/6bf4ebb5-969a-4841-b0a0-b74e4ade6b05" />

## Supported Telegram commands

Available commands:

**/get_whitelist:** Returns the whitelist location for current chat;

**/set_whitelist &lt;reader type&gt; &lt;location&gt; [params]:** Sets whitelist parameters for current chat;

**/get_option &lt;option name&gt;:** Get option value for current chat;

**/set_option &lt;option name&gt; &lt;option_value&gt;:** Set option value for current chat;

**/list_options:** List all options;

**/help:** Get help.

## Supported whitelist types
* [gspread](https://github.com/burnash/gspread): Google Spreadsheets.
