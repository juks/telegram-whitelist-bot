# What is it?
<img width="723" height="439" alt="image" src="https://github.com/user-attachments/assets/4a16ff48-17a4-4235-8ef3-a8ba1fb1f0a6" />

Simple bot that che checks the requests for users to join a telegram chat against given sources (whitelists). Those requests who is listed will be accepted automatically.

## Installation and running

* Install Docker Engine;
* Clone the repository;
* Copy .env.dist to .env and update your configuration;
* Execute _docker compose run --remove-orphans --build telegram-whitelist-bot_.

## How to use the bot
* Add bot to your Telegram chat;
* Give it admin permissions;
* Set the whilelist location.

## Supported Telegram commands

Available commands:

**/get_whitelist:** Returns the whitelist location for current chat;

**/set_whitelist &lt;reader type&gt; &lt;location&gt; [params]:** Sets whitelist parameters for current chat;

**/get_option &lt;option name&gt;:** Get option value for current chat;

**/set_option &lt;option name&gt; &lt;option_value&gt;:** Set option value for current chat;

**/list_options:** List all options;

**/help:** Get help.

## Supported whitelist types
* gspread: Google Spreadsheets.
