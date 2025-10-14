from wsgiref.handlers import BaseHandler

from lib.whitelist import Whitelist
from lib.options import Options
from lib.permanent import Permanent
import logging
from typing import Optional

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.constants import ChatMemberStatus

from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

class TgBot:
    token = ''
    app = None
    logger = None
    options = None
    permanent = None

    commands = {
        'get_whitelist':    {'args': [], 'description': 'Returns the whitelist location for current chat', 'admin': True},
        'set_whitelist':    {'args': ['reader type', 'location', 'column=0', 'sheet=0'], 'description': 'Sets the whitelist parameters for current chat', 'admin': True},
        'get_option':       {'args': ['option name'], 'description': 'Get option value for current chat', 'admin': True},
        'set_option':       {'args': ['option name', 'option_value'], 'description': 'Set option value for current chat', 'admin': True},
        'list_options':     {'args': [], 'description': 'List all options', 'admin': True},
        'help':             {'args': [], 'description': 'Get help'},
    }

    def __init__(self, token, config):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )

        # set higher logging level for httpx to avoid all GET and POST requests being logged
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)
        self.whitelist = Whitelist(config, self.logger)

        self.token = token
        self.app = Application.builder().token(token).build()

        self.options = Options({
            'enabled':      {'type': 'bool', 'description': 'Controls if the bot is active', 'default': True},
            'delete_declined':  {'type': 'bool', 'description': 'Delete declined requests'}
        })

        if 'pickle_file' in config:
            self.permanent = Permanent(config['pickle_file'], self.logger)
            data = self.permanent.restore()

            if data:
                if 'locations' in data:
                    self.whitelist.restore(data['locations'])

                if 'options' in data:
                    self.options.restore(data['options'])

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
                    f'Current whitelist is: {location['params']['location']} ({location['reader_type']}, column {location['params']['column']}, sheet {location['params']['sheet']})')

    async def cmd_set_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Set data source for this chat"""
        chat_id = update.effective_message.chat_id

        try:
            self.whitelist.set_whitelist_params(chat_id, context.args)

            if self.permanent:
                self.permanent.store('locations', self.whitelist.dump())

            await update.effective_chat.send_message('Setting new whitelist')
        except Exception as e:
            await update.effective_chat.send_message(f'Error setting new whitelist: {str(e)} ({type(e)})')

    async def cmd_get_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Getting bot option for given chat"""
        chat_id = update.effective_message.chat_id

        try:
            value = self.options.get_option(chat_id, context.args[0])
            if self.permanent:
                self.permanent.store('options', self.options.dump())

            await update.effective_chat.send_message(f'Option <b>{context.args[0]}</b> value is <b>{value}</b>', parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_chat.send_message(f'Error getting option value: {str(e)}')

    async def cmd_set_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Setting chat option for given chat"""
        chat_id = update.effective_message.chat_id

        try:
            self.options.set_option(chat_id, context.args[0], context.args[1])

            if self.permanent:
                self.permanent.store('options', self.options.dump())

            await update.effective_chat.send_message(f'Setting option {context.args[0]}')
        except Exception as e:
            await update.effective_chat.send_message(f'Error setting option value: {str(e)}')

    async def cmd_list_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all options"""
        await update.effective_chat.send_message('Options are:\n' + self.options.get_reference(),
                                                 parse_mode=ParseMode.HTML
                                                 )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get help"""
        result = ''

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

        await update.effective_chat.send_message('<b>Available commands:</b>\n' + result,
                                                 parse_mode=ParseMode.HTML
                                                 )

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
                if self.options.get_option(chat.id, 'delete_declined'):
                    await chat_join_request.decline()

                self.logger.info('User %s was banned in group %s', user.username, chat.title)
            elif await self.whitelist.check_allowed_user(chat.id, user.username):
                await chat_join_request.approve()

                self.logger.info(f'Join request approved for chat %s', chat.title)
            else:
                if self.options.get_option(chat.id, 'delete_declined'):
                    await chat_join_request.decline()

                self.logger.info('Join request declined for chat %s', chat.title)
        except Exception as e:
            self.logger.error(f'Error processing join request for chat %s: %s (%s)', chat.title, str(e), type(e))

    def extract_status_change(self, chat_member_update: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
        """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
        of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
        the status didn't change.
        """
        status_change = chat_member_update.difference().get("status")
        old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

        if status_change is None:
            return None

        old_status, new_status = status_change
        was_member = old_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
        is_member = new_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

        return was_member, is_member

    async def track_chats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Tracks the chats the bot is in."""
        result = self.extract_status_change(update.my_chat_member)
        if result is None:
            return
        was_member, is_member = result

        # Let's check who is responsible for the change
        cause_name = update.effective_user.full_name

        # Handle chat types differently:
        chat = update.effective_chat
        if chat.type == Chat.PRIVATE:
            if not was_member and is_member:
                # This may not be really needed in practice because most clients will automatically
                # send a /start command after the user unblocks the bot, and start_private_chat()
                # will add the user to "user_ids".
                # We're including this here for the sake of the example.
                self.logger.info("%s unblocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).add(chat.id)
            elif was_member and not is_member:
                self.logger.info("%s blocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).discard(chat.id)
        elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            if not was_member and is_member:
                self.logger.info("%s added the bot to the group %s", cause_name, chat.title)
                context.bot_data.setdefault("group_ids", set()).add(chat.id)
            elif was_member and not is_member:
                self.logger.info("%s removed the bot from the group %s", cause_name, chat.title)
                context.bot_data.setdefaПокult("group_ids", set()).discard(chat.id)
        elif not was_member and is_member:
            self.logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            self.logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)

    async def common_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Bot commands dispatcher"""
        user = update.effective_message.from_user
        message_text = update.effective_message.text
        command_with_bot_name = message_text.split(' ')[0]
        command_name = command_with_bot_name.split('@')[0][1:]

        if command_name not in self.commands:
            await update.effective_chat.send_message('Unknown command')
            return

        if 'admin' in self.commands[command_name] and self.commands[command_name]['admin'] is True:
            if not await self.is_admin(update, user.id):
                await update.effective_chat.send_message('Only admins can call this command')

                return

        obl_args_count = 0

        if 'args' in self.commands[command_name]:
            for arg in self.commands[command_name]['args']:
                parts = arg.split('=')

                if len(parts) == 1:
                    obl_args_count += 1

        if len(context.args) < obl_args_count:
            s = 's' if obl_args_count > 1 else ''
            await update.effective_chat.send_message(f'This command takes at least {obl_args_count} argument{s}')
            return

        handler = getattr(self, 'cmd_' + command_name)

        if not handler:
            await update.effective_chat.send_message(f'No handler for command {command_name}')
            return

        await handler(update, context)


    def run(self):
        """Start the bot"""
        for command in self.commands:
            self.app.add_handler(CommandHandler(command, self.common_handler))

        # Handle chat join request
        self.app.add_handler(ChatMemberHandler(self.track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
        self.app.add_handler(ChatJoinRequestHandler(self.join_request))

        self.app.run_polling(allowed_updates=Update.ALL_TYPES)