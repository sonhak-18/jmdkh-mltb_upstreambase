#!/usr/bin/env python3
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot import LOGGER, bot, bot_loop
from bot.helper.ext_utils.bot_utils import is_gdrive_link, new_thread, sync_to_async
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (auto_delete_message,
                                                      editMessage, sendMessage)

@new_thread
async def deletefile(client, message):
    args = message.text.split()
    if len(args) > 1:
        link = args[1]
    elif reply_to := message.reply_to_message:
        link = reply_to.text.split(maxsplit=1)[0].strip()
    else:
        link = ''
    if is_gdrive_link(link):
        LOGGER.info(link)
        drive = GoogleDriveHelper()
        msg = await sync_to_async(drive.deletefile, link)
    else:
        msg = 'Send Gdrive link along with command or by replying to the link by command'
    reply_message = await sendMessage(message, msg)
    await auto_delete_message(message, reply_message)

delete = set()

@new_thread
async def delete_leech(client, message):
    if len(message.command) == 1:
        link = message.command[0].strip()
    elif reply_to := message.reply_to_message:
        link = reply_to.text.split(maxsplit=1)[0].strip()
    else:
        link = ''
    if not link.startswith('https://t.me/'):
        msg = 'Send telegram message link along with command or by replying to the link by command'
        return await sendMessage(message, msg)
    if len(delete) != 0:
        msg = 'Already deleting in progress'
        return await sendMessage(message, msg)
    msg = f'Okay deleting all replies with {link}'
    link = link.split('/')
    message_id = int(link[-1])
    chat_id = link[-2]
    if chat_id.isdigit():
        chat_id = f'-100{chat_id}'
        chat_id = int(chat_id)
    reply_message = await sendMessage(message, msg)
    bot_loop.create_task(deleting(client, chat_id, message_id, reply_message))
    

async def deleting(client, chat_id, message_id, message):
    delete.add(message_id)
    try:
        msg = await client.get_messages(chat_id, message_id, replies=-1)
        replies_ids = []
        while msg:
            replies_ids.append(msg.id)
            if msg.media_group_id:
                media_group = await msg.get_media_group()
                media_ids = []
                for media in media_group:
                    media_ids.append(media.id)
                    msg = media.reply_to_message
                    if not msg:
                        msg = await client.get_messages(chat_id, media.reply_to_message_id, replies=-1)
                replies_ids.extend(media_ids)
            else:
                msg = msg.reply_to_message
        replies_ids = list(set(replies_ids))
        deleted = await client.delete_messages(chat_id, replies_ids)
        await editMessage(message, f'{deleted} message deleted')
    except Exception as e:
        await editMessage(message, str(e))
    delete.remove(message_id)

bot.add_handler(MessageHandler(deletefile, filters=command(BotCommands.DeleteCommand) & CustomFilters.sudo))
bot.add_handler(MessageHandler(delete_leech, filters=command(f'leech{BotCommands.DeleteCommand}') & CustomFilters.sudo))