from lib.tg_bot_base import TgBotBase
from lib.whitelist import Whitelist
from lib.options import Options
from lib.redis import Redis
import logging
from typing import Optional

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes, ChatJoinRequestHandler


class TgBot(TgBotBase):

    commands = {
        'get_whitelist':    {'args': [], 'description': 'Returns the whitelist location for current chat', 'admin': True},
        'test_whitelist':   {'args': [], 'description': 'Get some idea of what current whitelist contains', 'admin': True},
        'set_whitelist':    {'args': ['reader type', 'location=default', 'column=1', 'sheet=0'], 'description': 'Sets the whitelist parameters for current chat', 'admin': True},
        'set_whitelist_condition': {'args': ['condition'],
                          'description': 'Sets the whitelist parameters for current chat (where appropriate)', 'admin': True},
        'test_user':        {'args': ['username'], 'description': 'Check if user is allowed into chat'},
        'get_option':       {'args': ['option name'], 'description': 'Get option value for current chat', 'admin': True},
        'set_option':       {'args': ['option name', 'option_value'], 'description': 'Set option value for current chat', 'admin': True},
        'list_options':     {'args': [], 'description': 'List all options', 'admin': True},
        'start':            {'args': [], 'description': 'Get welcome message'},
        'help':             {'args': [], 'description': 'Get help'},
    }

    def __init__(self, token, config):
        super().__init__(token, config, commands=self.commands)

        # Initialize Redis client with parameters from config
        redis_host = config.get('redis_host', 'localhost')
        redis_port = config.get('redis_port', 6379)
        redis_client = Redis(host=redis_host, port=redis_port)

        self.whitelist = Whitelist(config, self.logger, redis_client=redis_client)

        self.options = Options({
            'enabled':                      {'type': 'bool', 'description': 'Controls if the bot is active', 'default': True},
            'delete_commands':              {'type': 'bool', 'description': 'Delete command messages', 'default': True},
            'delete_declined_requests':     {'type': 'bool', 'description': 'Delete declined requests'},
        }, redis_client=redis_client)

    async def is_admin(self, update: Update, user_id) -> bool:
        """Checks if a user is an administrator in the current chat."""
        if not update.effective_chat:
            return False  # Not in a chat context, or chat is not available

        member = await update.effective_chat.get_member(user_id)

        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

    async def cmd_get_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get data source for this chat"""
        chat_id = update.effective_message.chat_id

        location = self.whitelist.get_whitelist_params(chat_id)

        if location is None:
            await update.effective_chat.send_message('No whitelist for this chat')
        else:
            if 'is_default' in location:
                await update.effective_chat.send_message(
                    f'Current whitelist is: default')
            elif location['reader_type'] == 'gspread':
                await update.effective_chat.send_message(
                    f"Current whitelist is: {location['params']['location']} ({location['reader_type']}, column {location['params']['column']}, sheet {location['params']['sheet']})")
            elif location['reader_type'] == 'file':
                await update.effective_chat.send_message(
                    f"Current whitelist is: {location['params']['location']} ({location['reader_type']})")
            elif location['reader_type'] == 'api':
                token_note = 'with token' if 'token' in location['params'] and location['params']['token'] else 'no token'
                await update.effective_chat.send_message(
                    f"Current whitelist is: {location['params']['location']} ({location['reader_type']}, {token_note})")

    async def cmd_set_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Set data source for this chat"""
        chat_id = update.effective_message.chat_id

        self.whitelist.set_whitelist_params(chat_id, context.args)

        await update.effective_chat.send_message('Setting new whitelist')

    async def cmd_test_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test if user with given username is allowed"""
        chat_id = update.effective_message.chat_id

        result = await self.whitelist.check_allowed_user(chat_id, context.args[0])

        if result:
            await update.effective_chat.send_message(f'User {context.args[0]} is allowed')
        else:
            await update.effective_chat.send_message(f'User {context.args[0]} is not allowed')


    async def cmd_test_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get 3 masked usernames for this chat"""
        chat_id = update.effective_message.chat_id

        check_result = await self.whitelist.test(chat_id)

        if isinstance(check_result, list):
            await update.effective_chat.send_message('Whitelist test result is: ' + ', '.join(check_result))
        else:
            await update.effective_chat.send_message('Whitelist test result is: ' + check_result)

    async def cmd_set_whitelist_condition(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Set data source for this chat"""
        chat_id = update.effective_message.chat_id

        await self.whitelist.set_whitelist_condition(chat_id, ' '.join(context.args))

        await update.effective_chat.send_message('Setting whitelist condition')


    async def cmd_get_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Getting bot option for given chat"""
        chat_id = update.effective_message.chat_id

        value = self.options.get_option(chat_id, context.args[0])

        await update.effective_chat.send_message(f'Option <b>{context.args[0]}</b> value is <b>{value}</b>', parse_mode=ParseMode.HTML)

    async def cmd_set_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Setting chat option for given chat"""
        chat_id = update.effective_message.chat_id

        self.options.set_option(chat_id, context.args[0], context.args[1])

        await update.effective_chat.send_message(f'Setting option {context.args[0]}')

    async def cmd_list_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all options"""
        await update.effective_chat.send_message('Options are:\n' + self.options.get_reference(),
                                                 parse_mode=ParseMode.HTML
                                                 )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        start_message = "<b>Whitelist Bouncer Bot</b>\n"
        start_message += "Simple bot that adds whitelist automation to Telegram chats. Those users requests who is listed in chat whitelist will be accepted automatically.\n\n"
        start_message += "<b>Source and manual:</b> http://bit.ly/4o0gkji\n"

        start_message += "\n" + self.help_message()

        await update.effective_chat.send_message(start_message,
                                                 parse_mode=ParseMode.HTML
                                                 )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get help"""
        help_message = self.help_message()

        await update.effective_chat.send_message(help_message,
                                                 parse_mode=ParseMode.HTML
                                                 )

    def help_message(self) -> str:
        result = '<b>Available commands:</b>\n'

        for command in self.commands:
            result += f'<b>/{command}</b>'

            if 'args' in self.commands[command]:
                for arg in self.commands[command]['args']:
                    parts = arg.split('=')

                    if len(parts) == 1:
                        da = '&lt;'
                        db = '&gt;'
                    else:
                        da = '['
                        db = ']'

                    result += f' {da}{arg}{db}'

            result += ': ' + self.commands[command]['description'] + '\n'

        return result

    async def join_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process join request"""
        chat_join_request = update.chat_join_request
        user = chat_join_request.from_user
        chat = chat_join_request.chat

        self.logger.info('New join request from user %s to the group %s', user.username, chat.title)

        if not self.options.get_option(chat.id, 'enabled'):
            self.logger.info('Bot is disabled')

        chat_member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)

        try:
            if chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER,
                                      ChatMemberStatus.RESTRICTED]:
                await chat_join_request.decline()

                self.logger.info('User %s in already a sort of member of group %s', user.username, chat.title)
            elif chat_member.status in [ChatMemberStatus.BANNED]:
                if self.options.get_option(chat.id, 'delete_declined_requests'):
                    await chat_join_request.decline()

                self.logger.info('User %s was banned in group %s', user.username, chat.title)
            elif await self.whitelist.check_allowed_user(chat.id, user.username):
                await chat_join_request.approve()

                self.logger.info(f'Join request approved for user %s into the chat %s', user.username, chat.title)
            else:
                self.logger.info(f'User %s is not allowed into the group %s', user.username, chat.title)

                if self.options.get_option(chat.id, 'delete_declined_requests'):
                    await chat_join_request.decline()
                    self.logger.info('Join request declined for chat %s', chat.title)
                    
        except Exception as e:
            self.logger.error(f'Error processing join request for chat %s: %s (%s)', chat.title, str(e), type(e))

    # help_message, join_request, cmd_* methods remain here in subclass

    def run(self):
        # Register chat join request handler in subclass
        self.app.add_handler(ChatJoinRequestHandler(self.join_request))
        # Then delegate to base to register commands, tracking, and start polling
        return super().run()