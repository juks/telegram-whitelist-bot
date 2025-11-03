import logging
from typing import Optional

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)


class TgBotBase:
    token = ''
    app = None
    logger = None
    commands = {}
    config = None
    options = None

    def __init__(self, token, config, commands):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )

        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)

        self.token = token
        self.config = config
        self.commands = commands
        self.app = Application.builder().token(token).build()

    async def is_admin(self, update: Update, user_id) -> bool:
        if not update.effective_chat:
            return False

        member = await update.effective_chat.get_member(user_id)
        from telegram.constants import ChatMemberStatus

        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

    def extract_status_change(self, chat_member_update: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
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
        result = self.extract_status_change(update.my_chat_member)
        if result is None:
            return
        was_member, is_member = result

        cause_name = update.effective_user.full_name

        chat = update.effective_chat
        from telegram import Chat as TgChat
        if chat.type == TgChat.PRIVATE:
            if not was_member and is_member:
                self.logger.info("%s unblocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).add(chat.id)
            elif was_member and not is_member:
                self.logger.info("%s blocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).discard(chat.id)
        elif chat.type in [TgChat.GROUP, TgChat.SUPERGROUP]:
            if not was_member and is_member:
                self.logger.info("%s added the bot to the group %s", cause_name, chat.title)
                context.bot_data.setdefault("group_ids", set()).add(chat.id)
            elif was_member and not is_member:
                self.logger.info("%s removed the bot from the group %s", cause_name, chat.title)
                context.bot_data.setdefault("group_ids", set()).discard(chat.id)
        elif not was_member and is_member:
            self.logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            self.logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)

    async def common_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_message.from_user
        message_text = update.effective_message.text
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id

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

        try:
            await handler(update, context)
        except Exception as e:
            await update.effective_chat.send_message(str(e))
            self.logger.info('Command handler error: %s', str(e), exc_info=True)

        if self.options and self.options.get_option(chat_id, 'delete_commands'):
            await context.bot.delete_message(chat_id, message_id)
        return

    def run(self):
        for command in self.commands:
            self.app.add_handler(CommandHandler(command, self.common_handler))

        self.app.add_handler(ChatMemberHandler(self.track_chats, ChatMemberHandler.MY_CHAT_MEMBER))


        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


