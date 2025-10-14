#!/usr/bin/env python
import argparse
from lib.tg_bot import TgBot
from lib.envdefault import EnvDefault

def main() -> None:
    parser = argparse.ArgumentParser(description="Runtime parameters",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-pf', '--pickle_file',          action=EnvDefault, envvar='PICKLE_FILE',    help='Path to pickle file')
    parser.add_argument('-gsa', '--gsa_file',            action=EnvDefault, envvar='GSA_FILE',       help='Path to google service account file')
    parser.add_argument('-tg_token', '--telegram_token', action=EnvDefault, envvar='TELEGRAM_TOKEN', help='Telegram token', required=True)
    parser.add_argument('-ds', '--default_source',       action=EnvDefault, envvar='DEFAULT_SOURCE', help='Default whilelist source')

    args = parser.parse_args()
    config = vars(args)

    bot = TgBot(config['telegram_token'], config)
    bot.run()

if __name__ == "__main__":
    main()