# What is it?
<img width="600" alt="image" src="https://github.com/user-attachments/assets/4a16ff48-17a4-4235-8ef3-a8ba1fb1f0a6" />

Simple [bot](https://t.me/whitelist_bouncer_bot) that adds whitelist automation to Telegram chats. Those users requests who is listed in chat whitelist will be accepted automatically.

## Installation and running

* Install Docker Engine;
* Clone the repository;
* Copy .env.dist to .env and update your configuration;
* Execute _docker compose up --force-recreate --remove-orphans --build telegram-whitelist-bot_.

## How to use the bot
* Add bot to your Telegram chat (@whitelist_bouncer_bot or an instance of your own);
* Grant admin permissions to the bot;
* Set the whilelist location.
* Grant whitelist access permissions when necessary.
* Create moderated invitation link.

<img width="350" alt="image" src="https://github.com/user-attachments/assets/6bf4ebb5-969a-4841-b0a0-b74e4ade6b05" />

## Supported Telegram commands

Available commands:

**/get_whitelist:** Returns the whitelist location for current chat;

**/test_whitelist:** Get whitelist reading (check user Bob in case of API or get first three whitelist entries);

**/set_whitelist &lt;reader type&gt; &lt;location&gt; [params]:** Sets whitelist parameters for current chat;

**/get_option &lt;option name&gt;:** Get option value for current chat;

**/set_option &lt;option name&gt; &lt;option_value&gt;:** Set option value for current chat;

**/list_options:** List all options;

**/help:** Get help.

## Supported whitelist types
### • api: remote whitelist available via the HTTP(s) API
To test the api you may run a local web server:
```
python3 src/misc/test_api.py --port 8080 --token secret123
```

Test the server response with Curl:
```
$ curl -H 'Authorization: Bearer secret123' 'http://localhost:8080/check-user/JohnDoe'
{"result": true}
```

Then set up the reader and check whitelist test.

Wrong token to see the error:
```
/set_whitelist@whitelist_bouncer_bot api http://localhost:8080/check-user/{username} secret12345
/test_whitelist@whitelist_bouncer_bot

Whitelist test result is: user bob is not allowed: HTTP Error 401: Unauthorized
```

Correct token:
```
/set_whitelist@whitelist_bouncer_bot api http://localhost:8080/check-user/{username} secret123
/test_whitelist@whitelist_bouncer_bot

Whitelist test result is: user bob is allowed
```

### • [gspread](https://github.com/burnash/gspread): Google Spreadsheets
Example whitelist with usernames listed in column 1, sheet 0:

<img width="300" alt="image" src="https://github.com/user-attachments/assets/c4c6ca23-c341-4c84-b104-413d46fd13f6" />

```
/set_whitelist@whitelist_bouncer_bot gspread https://docs.google.com/spreadsheets/d/somesheetid 1 0
```

Some column conditions can be implemented using "condition" option:

<img width="300" alt="image" src="https://github.com/user-attachments/assets/a237f340-690f-43b7-983b-369823220d08" />

Default source defined in .env:
```
DEFAULT_SOURCE=gspread;location=https://docs.google.com/spreadsheets/d/some_id;condition=2 in ("yes", "yeap");sheet=1;column=1
```

To use public bot @whitelist_bouncer_bot you need to grant spreadsheet access to serivce accout:
```
driveaccess@telegram-whitelist-bouncer.iam.gserviceaccount.com
```

### • file: online text file with usernames list
```
/set_whitelist@whitelist_bouncer_bot file https://my.domain.com/users.txt
```

## Project structure
```
telegram-whitelist-bot/
|-- src/                              - Source code
|   |-- data.pickle                   - Sample runtime state file for dev/testing
|   |-- main.py                       - Entry point: parses CLI/env, starts TgBot
|   |-- lib/                          - Core modules
|   |   |-- envdefault.py             - argparse action to read defaults from environment
|   |   |-- options.py                - In-memory options storage and reference/validation
|   |   |-- permanent.py              - Pickle-based persistence for locations/options
|   |   |-- reader_file.py            - Reader: usernames from text file by URL
|   |   |-- reader_gspread.py         - Reader: usernames from Google Sheets
|   |   |-- reader_api.py             - Reader: single-user check via REST API (Bearer auth)
|   |   |-- tg_bot.py                 - Telegram bot logic and command handlers
|   |   `-- whitelist.py              - Reader registry, chat-to-source mapping, access checks
|   `-- misc/                         - Auxiliary tools and test utilities
|       `-- test_api.py               - Minimal HTTP server to test ReaderApi
|-- data.pickle                       - Example persisted state (locations/options)
|-- docker-compose.yml                - Compose file to run the bot in Docker
|-- Dockerfile                        - Docker build definition for the bot
|-- README.md                         - Project overview and usage instructions
`-- requirements.txt                  - Python dependencies
```
