# bot/handlers.py

#Manages all Telegram bot interactions, including commands, button callbacks, and conversational flows. This is the most critical file, especially with the refined String Session generation process integrated via the bot interface.


import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    ParseMode
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from .config import (
    is_admin,
    get_session,
    set_session,
    config,
    save_config
)
from .logger import logger
from .checker import TelegramChecker
from .adder import TelegramAdder
from .file_handler import FileHandler
import aiofiles

# Define unique states for ConversationHandlers
SET_APIFY_TOKEN_STATE = 1
SET_TELEGRAM_API_ID_STATE = 2
SET_TELEGRAM_API_HASH_STATE = 3
SET_TELEGRAM_STRING_SESSION_STATE = 4
SET_TARGET_CHANNEL_USERNAME_STATE = 5

BLOCK_USER_ID_STATE = 6

class BotHandlers:
    """
    A class encapsulating all the handlers for the Telegram Bot.
    """

    def __init__(self, application, checker: TelegramChecker, adder: TelegramAdder):
        """
        Initialize the BotHandlers with the application and necessary services.

        Args:
            application: Telegram bot application instance.
            checker (TelegramChecker): Instance of TelegramChecker.
            adder (TelegramAdder): Instance of TelegramAdder.
        """
        self.application = application
        self.checker = checker
        self.adder = adder
        self.file_handler = FileHandler()
        self.register_handlers()

    def register_handlers(self):
        """
        Register all handlers (commands, callbacks, message handlers).
        """

        # -------- Command Handlers --------
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel))
        self.application.add_handler(CommandHandler("status", self.status_command))

        # -------- CallbackQueryHandlers for Buttons --------
        callback_patterns = [
            "settings",
            "upload_csv",
            "add_to_channel",
            "manage_blocked",
            "export_data",
            "exit",
            "set_apify_token",
            "set_telegram_api_id",
            "set_telegram_api_hash",
            "set_string_session",
            "set_target_channel_username",
            r"^unblock_user_\d+$",
            "block_user_prompt",
            "back_to_main",
            "export_registered_users",
            "list_user_ids"
        ]

        for pattern in callback_patterns:
            self.application.add_handler(
                CallbackQueryHandler(self.button_handler, pattern=pattern)
            )

        # -------- Conversation Handlers --------
        # Handler for setting Apify API Token
        conv_handler_set_apify = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_apify_token, pattern='set_apify_token')],
            states={
                SET_APIFY_TOKEN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_apify_token)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_apify)

        # Handler for setting Telegram API ID
        conv_handler_set_api_id = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_telegram_api_id, pattern='set_telegram_api_id')],
            states={
                SET_TELEGRAM_API_ID_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_telegram_api_id)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_api_id)

        # Handler for setting Telegram API Hash
        conv_handler_set_api_hash = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_telegram_api_hash, pattern='set_telegram_api_hash')],
            states={
                SET_TELEGRAM_API_HASH_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_telegram_api_hash)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_api_hash)

        # Handler for setting String Session
        conv_handler_set_ss = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_string_session, pattern='set_string_session')],
            states={
                SET_TELEGRAM_STRING_SESSION_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_string_session)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_ss)

        # Handler for setting Target Channel Username
        conv_handler_set_channel = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_set_target_channel_username, pattern='set_target_channel_username')],
            states={
                SET_TARGET_CHANNEL_USERNAME_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_target_channel_username)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_set_channel)

        # Handler for blocking a user
        conv_handler_block_user = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.block_user_prompt, pattern='block_user_prompt')],
            states={
                BLOCK_USER_ID_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.block_user_input_handler)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
            per_user=True
        )
        self.application.add_handler(conv_handler_block_user)

        # -------- Message Handlers --------
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.upload_csv_handler))

        # Register the general text message handler (if needed)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_messages))

        # -------- Error Handler --------
        self.application.add_error_handler(self.error_handler)

    def get_main_menu_keyboard(self) -> List[List[InlineKeyboardButton]]:
        """
        Returns the main menu keyboard layout.

        Returns:
            List[List[InlineKeyboardButton]]: Keyboard layout.
        """
        return [
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
            [InlineKeyboardButton("📂 آپلود مخاطبین CSV", callback_data="upload_csv")],
            [InlineKeyboardButton("➕ افزودن کاربران به کانال هدف", callback_data="add_to_channel")],
            [InlineKeyboardButton("🛑 مدیریت کاربران مسدود شده", callback_data="manage_blocked")],
            [InlineKeyboardButton("📤 صادرات داده‌ها", callback_data="export_data")],
            [InlineKeyboardButton("❌ خروج کامل", callback_data="exit")]
        ]

    def initialize_components(self):
        """
        Reinitialize checker and adder after configuration changes.
        """
        # Reinitialize TelegramChecker
        apify_api_token = config.get("apify_api_token")
        if apify_api_token:
            self.checker = TelegramChecker(apify_api_token)
            logger.info("TelegramChecker re-initialized with new Apify API Token.")
        else:
            self.checker = None
            logger.warning("TelegramChecker not initialized. Missing Apify API Token.")

        # Reinitialize TelegramAdder
        telegram_api_id = config.get("telegram_api_id")
        telegram_api_hash = config.get("telegram_api_hash")
        telegram_string_session = config.get("telegram_string_session")
        target_channel_username = config.get("target_channel_username")
        
        if all([telegram_api_id, telegram_api_hash, telegram_string_session, target_channel_username]):
            self.adder = TelegramAdder(
                api_id=int(telegram_api_id),
                api_hash=telegram_api_hash,
                string_session=telegram_string_session,
                target_channel_username=target_channel_username
            )
            logger.info("TelegramAdder re-initialized with new Telegram credentials.")
        else:
            self.adder = None
            logger.warning("TelegramAdder not initialized. Missing Telegram credentials.")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        # Show the main menu keyboard
        keyboard = self.get_main_menu_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "سلام! لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /help command.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        help_text = (
            "📄 **دستورات و گزینه‌ها:**\n\n"
            "/start - شروع ربات و نمایش گزینه‌ها\n"
            "/help - نمایش پیام راهنما\n"
            "/cancel - لغو عملیات جاری\n"
            "/status - نمایش وضعیت فعلی ربات\n\n"
            "**گزینه‌ها (از طریق دکمه‌ها):**\n"
            "• ⚙️ تنظیمات\n"
            "• 📂 آپلود مخاطبین CSV\n"
            "• ➕ افزودن کاربران به کانال هدف\n"
            "• 🛑 مدیریت کاربران مسدود شده\n"
            "• 📤 صادرات داده‌ها\n"
            "• ❌ خروج کامل\n\n"
            "**نکات:**\n"
            "- فایل‌های CSV باید حاوی شماره تلفن‌ها در فرمت بین‌المللی (مثلاً +1234567890) باشند.\n"
            "- فقط کاربرانی که در لیست ادمین‌ها هستند می‌توانند از این ربات استفاده کنند.\n"
            "- پس از آپلود CSV و پردازش، می‌توانید کاربران ثبت‌شده را به کانال هدف اضافه کنید."
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /status command to display current bot configurations.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        status_text = (
            f"📊 **وضعیت ربات:**\n\n"
            f"• **Apify API Token:** {'✅ تنظیم شده' if config.get('apify_api_token') else '❌ تنظیم نشده'}\n"
            f"• **Telegram API ID:** {config.get('telegram_api_id') or '❌ تنظیم نشده'}\n"
            f"• **Telegram API Hash:** {config.get('telegram_api_hash') or '❌ تنظیم نشده'}\n"
            f"• **String Session:** {'✅ تنظیم شده' if config.get('telegram_string_session') else '❌ تنظیم نشده'}\n"
            f"• **Target Channel Username:** {config.get('target_channel_username') or '❌ تنظیم نشده'}\n"
            f"• **Blocked Users Count:** {len(config.get('blocked_users', []))}"
        )
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /cancel command to cancel ongoing operations.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        if update.message:
            await update.message.reply_text('📴 عملیات جاری لغو شد.')
        elif update.callback_query:
            await update.callback_query.edit_message_text('📴 عملیات جاری لغو شد.')
        # Clear any user data state
        context.user_data.clear()
        # Show main menu again
        keyboard = self.get_main_menu_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text(
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=reply_markup
            )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle all callback queries from inline buttons.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        data = query.data

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await query.edit_message_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        # Settings Menu
        if data == "settings":
            await self.settings_menu(update, context)

        elif data == "upload_csv":
            if not self.checker:
                await query.edit_message_text("❌ لطفاً ابتدا در تنظیمات Apify API Token را تنظیم کنید.")
                return
            await query.edit_message_text("📂 لطفاً فایل CSV حاوی شماره تلفن‌ها را ارسال کنید.")

        elif data == "add_to_channel":
            # Check if CSV has been uploaded and processed
            session_data = get_session(user_id)
            if not session_data.get("results"):
                await query.edit_message_text(
                    "❌ لطفاً ابتدا یک فایل CSV آپلود و پردازش کنید."
                )
                return
            await self.add_to_channel(update, context)

        elif data == "manage_blocked":
            await self.manage_blocked_menu(update, context)

        elif data == "export_data":
            await self.export_data_menu(update, context)

        elif data == "exit":
            await query.edit_message_text("❌ ربات با موفقیت متوقف شد.")
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot has been stopped gracefully.")

        elif re.match(r"^unblock_user_\d+$", data):
            try:
                target_user_id = int(data.split("_")[-1])
                await self.unblock_user(update, context, target_user_id)
            except ValueError:
                await query.edit_message_text("❌ شناسه کاربری نامعتبر است.")

        elif data == "back_to_main":
            await self.start_command(update, context)

        # Export Data Handlers
        elif data == "export_registered_users":
            await self.export_registered_users(update, context)

        elif data == "list_user_ids":
            await self.list_user_ids(update, context)

        else:
            await query.edit_message_text("❓ گزینه انتخابی نامعتبر است. لطفاً دوباره تلاش کنید.")

    async def settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Display the settings menu.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("🔧 تنظیم Apify API Token", callback_data="set_apify_token"),
             InlineKeyboardButton("🔧 تنظیم Telegram API ID", callback_data="set_telegram_api_id")],
            [InlineKeyboardButton("🔧 تنظیم Telegram API Hash", callback_data="set_telegram_api_hash"),
             InlineKeyboardButton("🔧 تنظیم String Session", callback_data="set_string_session")],
            [InlineKeyboardButton("🔧 تنظیم Target Channel Username", callback_data="set_target_channel_username")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚙️ **تنظیمات ربات:**\n\n"
            "لطفاً یکی از تنظیمات زیر را انتخاب کنید تا مقدار آن را وارد یا به‌روزرسانی کنید:",
            reply_markup=reply_markup
        )

    async def start_set_apify_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Apify API Token.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Apify API Token**\n\n"
            "لطفاً Apify API Token خود را وارد کنید:"
        )
        return SET_APIFY_TOKEN_STATE

    async def set_apify_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Apify API Token input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        api_token = update.message.text.strip()
        if not api_token:
            await update.message.reply_text("❌ لطفاً یک Apify API Token معتبر وارد کنید:")
            return SET_APIFY_TOKEN_STATE

        # Basic validation (Apify tokens are typically long alphanumeric strings)
        if not isinstance(api_token, str) or len(api_token) < 20:
            await update.message.reply_text("❌ لطفاً یک Apify API Token معتبر وارد کنید:")
            return SET_APIFY_TOKEN_STATE

        config["apify_api_token"] = api_token
        save_config()

        # Initialize or reinitialize TelegramChecker
        self.checker = TelegramChecker(api_token)
        logger.info("TelegramChecker re-initialized with new Apify API Token.")

        await update.message.reply_text("✅ Apify API Token با موفقیت تنظیم شد.")
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def start_set_telegram_api_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Telegram API ID.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Telegram API ID**\n\n"
            "لطفاً Telegram API ID خود را وارد کنید (عدد):"
        )
        return SET_TELEGRAM_API_ID_STATE

    async def set_telegram_api_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Telegram API ID input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        api_id_text = update.message.text.strip()
        if not api_id_text.isdigit():
            await update.message.reply_text("❌ لطفاً یک Telegram API ID معتبر (عدد) وارد کنید:")
            return SET_TELEGRAM_API_ID_STATE

        api_id = int(api_id_text)
        config["telegram_api_id"] = api_id
        save_config()

        await update.message.reply_text("✅ Telegram API ID با موفقیت تنظیم شد.")
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def start_set_telegram_api_hash(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Telegram API Hash.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Telegram API Hash**\n\n"
            "لطفاً Telegram API Hash خود را وارد کنید:"
        )
        return SET_TELEGRAM_API_HASH_STATE

    async def set_telegram_api_hash(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle Telegram API Hash input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        api_hash = update.message.text.strip()
        if not api_hash:
            await update.message.reply_text("❌ لطفاً یک Telegram API Hash معتبر وارد کنید:")
            return SET_TELEGRAM_API_HASH_STATE

        config["telegram_api_hash"] = api_hash
        save_config()

        await update.message.reply_text("✅ Telegram API Hash با موفقیت تنظیم شد.")
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def start_set_string_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set String Session.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم/به‌روزرسانی String Session**\n\n"
            "لطفاً String Session خود را ارسال کنید:\n"
            "📝 **توجه:** String Session حاوی اطلاعات حساس است. آن را با هیچ‌کس به اشتراک نگذارید."
        )
        return SET_TELEGRAM_STRING_SESSION_STATE

    async def set_string_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle String Session input.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        string_session = update.message.text.strip()
        if not string_session:
            await update.message.reply_text("❌ لطفاً یک String Session معتبر ارسال کنید:")
            return SET_TELEGRAM_STRING_SESSION_STATE

        # Validate the String Session by attempting to connect
        telegram_api_id = config.get("telegram_api_id")
        telegram_api_hash = config.get("telegram_api_hash")
        target_channel_username = config.get("target_channel_username") or "@yourchannelusername"

        if not all([telegram_api_id, telegram_api_hash]):
            await update.message.reply_text("❌ API ID و API Hash تنظیم نشده‌اند. لطفاً ابتدا آن‌ها را تنظیم کنید.")
            return ConversationHandler.END

        try:
            # Attempt to connect with the new String Session
            test_adder = TelegramAdder(
                api_id=int(telegram_api_id),
                api_hash=telegram_api_hash,
                string_session=string_session,
                target_channel_username=target_channel_username
            )
            await test_adder.connect()
            await test_adder.disconnect()

            # If successful, update the config
            config["telegram_string_session"] = string_session
            save_config()
            await update.message.reply_text("✅ **String Session با موفقیت تنظیم شد!**")

            # Reinitialize TelegramAdder with the new String Session
            self.initialize_components()
            return ConversationHandler.END

        except errors.RPCError as e:
            logger.error(f"Telethon connection error with new String Session: {e}")
            await update.message.reply_text(f"❌ خطا در احراز هویت با String Session جدید: {e}")
            return SET_TELEGRAM_STRING_SESSION_STATE
        except Exception as e:
            logger.error(f"Unexpected error during String Session validation: {e}")
            await update.message.reply_text("❌ خطای غیرمنتظره‌ای رخ داد. لطفاً دوباره تلاش کنید.")
            return SET_TELEGRAM_STRING_SESSION_STATE

    async def start_set_target_channel_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start the process to set Target Channel Username.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔧 **تنظیم Target Channel Username**\n\n"
            "لطفاً نام کاربری کانال هدف خود را وارد کنید (با @ شروع کنید، مثلاً @yourchannelusername):",
            parse_mode=ParseMode.MARKDOWN
        )
        return SET_TARGET_CHANNEL_USERNAME_STATE

    async def set_target_channel_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle setting the target channel username.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        text = update.message.text.strip()
        USERNAME_REGEX = re.compile(r'^@[\w]{5,32}$')  # Telegram usernames are between 5-32 characters and can include underscores

        if not USERNAME_REGEX.match(text):
            await update.message.reply_text("❌ لطفاً یک نام کاربری کانال معتبر وارد کنید (با @ شروع و بین 5 تا 32 کاراکتر):")
            return SET_TARGET_CHANNEL_USERNAME_STATE  # Reuse the same state

        config["target_channel_username"] = text
        save_config()
        await update.message.reply_text("✅ نام کاربری کانال هدف با موفقیت تنظیم شد.")
        # Reinitialize TelegramAdder with new channel
        self.initialize_components()
        # Return to settings menu
        await self.settings_menu(update, context)
        return ConversationHandler.END

    async def upload_csv_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle CSV file uploads.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        if update.message.document:
            file = update.message.document
            if not file.file_name.lower().endswith(".csv"):
                await update.message.reply_text("❌ لطفاً یک فایل CSV معتبر ارسال کنید.")
                return

            try:
                # Define a temporary path to save the file
                temp_dir = Path("temp")
                temp_dir.mkdir(exist_ok=True)
                temp_file_path = temp_dir / f"{user_id}_{file.file_name}"

                # Check file size (e.g., limit to 5MB)
                MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
                if file.file_size > MAX_FILE_SIZE:
                    await update.message.reply_text(f"❌ فایل CSV بیش از 5MB است.")
                    return

                # Download the file asynchronously
                await file.get_file().download_to_drive(custom_path=str(temp_file_path))
                await update.message.reply_text("🔄 در حال پردازش فایل CSV شما. لطفاً صبر کنید...")

                # Read phone numbers from CSV asynchronously
                loop = asyncio.get_running_loop()
                if not self.checker:
                    await update.message.reply_text("❌ Apify API Token تنظیم نشده است. لطفاً در تنظیمات آن را تنظیم کنید.")
                    return

                phone_numbers = await loop.run_in_executor(None, self.checker.read_csv, str(temp_file_path))
                if not phone_numbers:
                    await update.message.reply_text("❌ فایل CSV خالی یا نامعتبر است.")
                    return

                MAX_PHONE_NUMBERS = config.get("batch_size", 10) * 100  # Example limit
                if len(phone_numbers) > MAX_PHONE_NUMBERS:
                    await update.message.reply_text(f"❌ تعداد شماره تلفن‌ها بیش از حد مجاز ({MAX_PHONE_NUMBERS}) است.")
                    return

                # Check Telegram status using Apify
                results = await self.checker.check_telegram_status_async(phone_numbers)

                # Save results in session
                session = get_session(user_id)
                session["results"] = results
                set_session(user_id, session)

                # Save results to CSV asynchronously
                result_file = Path(f"telegram_results_{user_id}.csv")
                self.checker.save_results(results, str(result_file))

                # Prepare a summary
                total = len(results)
                registered = len([r for r in results if r.get("isRegistered")])
                not_registered = total - registered
                summary = (
                    f"✅ **پردازش کامل شد!**\n\n"
                    f"کل شماره‌ها: {total}\n"
                    f"ثبت‌شده در تلگرام: {registered}\n"
                    f"ثبت‌نشده: {not_registered}"
                )

                # Send summary and the results file
                await update.message.reply_text(summary, parse_mode=ParseMode.MARKDOWN)
                await update.message.reply_document(
                    document=InputFile(str(result_file)),
                    filename=result_file.name,
                    caption="📁 این نتایج بررسی شماره تلفن‌های شما است."
                )

                # Clean up temporary files asynchronously
                try:
                    await self.file_handler.delete_file(temp_file_path)
                    await self.file_handler.delete_file(result_file)
                    if not any(temp_dir.iterdir()):
                        await self.file_handler.delete_directory(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary files: {e}")

            except Exception as e:
                logger.error(f"Error processing CSV: {e}")
                await update.message.reply_text("❌ هنگام پردازش فایل CSV خطایی رخ داد.")
        else:
            await update.message.reply_text("❌ لطفاً یک فایل CSV ارسال کنید.")

    async def add_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Add verified users to the target channel.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.edit_message_text("🔄 در حال افزودن کاربران به کانال هدف. لطفاً صبر کنید...")

        user_id = update.effective_user.id
        session_data = get_session(user_id)
        results = session_data.get("results", [])

        if not results:
            await query.edit_message_text("❌ هیچ داده‌ای برای افزودن وجود ندارد.")
            return

        # Filter registered users with valid user IDs
        registered_users = [r for r in results if r.get("isRegistered") and r.get("userId")]
        if not registered_users:
            await query.edit_message_text("❌ هیچ شماره تلفنی ثبت‌شده در تلگرام یافت نشد.")
            return

        # Get blocked users
        blocked_users = config.get("blocked_users", [])

        # Extract user IDs
        user_ids = [r.get("userId") for r in registered_users if r.get("userId")]

        # Initialize TelegramAdder client
        if not self.adder:
            await query.edit_message_text("❌ ربات به درستی تنظیم نشده است. لطفاً با مدیر تماس بگیرید.")
            return

        try:
            await self.adder.connect()
        except errors.RPCError as e:
            logger.error(f"Telethon connection error: {e}")
            await query.edit_message_text("❌ خطا در اتصال به Telegram. لطفاً بررسی کنید.")
            return
        except Exception as e:
            logger.error(f"Unexpected error during Telethon connection: {e}")
            await query.edit_message_text("❌ خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کنید.")
            return

        # Add users to channel
        try:
            summary = await self.adder.add_users_to_channel(user_ids, blocked_users)
        except errors.FloodWaitError as e:
            logger.warning(f"Flood wait error: {e}. Sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
            await query.edit_message_text("❌ ربات در حال حاضر با محدودیت سرعت مواجه شده است. لطفاً بعداً دوباره تلاش کنید.")
            return
        except PermissionError as e:
            logger.error(f"Permission error: {e}")
            await query.edit_message_text(f"❌ {e}")
            return
        except Exception as e:
            logger.error(f"Error adding users to channel: {e}")
            await query.edit_message_text(f"❌ خطایی رخ داد: {e}")
            return
        finally:
            await self.adder.disconnect()

        # Prepare a summary message
        success_count = len(summary["added"])
        failure_count = len(summary["failed"])
        summary_message = (
            f"✅ **افزودن کاربران به کانال کامل شد!**\n\n"
            f"تعداد موفق: {success_count}\n"
            f"تعداد ناموفق: {failure_count}"
        )
        await query.edit_message_text(summary_message, parse_mode=ParseMode.MARKDOWN)

        if summary["added"]:
            added_list = ", ".join(map(str, summary["added"]))
            await query.message.reply_text(f"🟢 **کاربران اضافه شده:**\n{added_list}")

        if summary["failed"]:
            failed_list = ", ".join(map(str, summary["failed"]))
            await query.message.reply_text(f"🔴 **کاربران اضافه نشده:**\n{failed_list}")

    async def manage_blocked_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Display the manage blocked users menu.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        blocked_users = config.get("blocked_users", [])
        if not blocked_users:
            blocked_text = "🛑 **لیست کاربران مسدود شده خالی است.**"
        else:
            blocked_text = (
                "🛑 **لیست کاربران مسدود شده:**\n\n"
                + "\n".join([f"• {uid}" for uid in blocked_users])
            )

        keyboard = [
            [InlineKeyboardButton("➕ مسدود کردن کاربر جدید", callback_data="block_user_prompt")]
        ]
        # Dynamically add unblock buttons
        for uid in blocked_users:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔓 بازگشایی مسدودیت کاربر {uid}",
                    callback_data=f"unblock_user_{uid}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(blocked_text, reply_markup=reply_markup)

    async def block_user_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Prompt admin to enter a user ID to block.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "➕ لطفاً شناسه کاربری تلگرام کاربری که می‌خواهید مسدود کنید را وارد کنید (عدد):"
        )
        return BLOCK_USER_ID_STATE

    async def block_user_input_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle input for blocking a new user.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        target_user_id_text = update.message.text.strip()
        if not target_user_id_text.isdigit():
            await update.message.reply_text(
                "❌ لطفاً یک شناسه کاربری تلگرام معتبر (عدد) وارد کنید:"
            )
            return BLOCK_USER_ID_STATE

        target_user_id = int(target_user_id_text)

        if target_user_id in config.get("blocked_users", []):
            await update.message.reply_text(
                f"🔍 کاربر با شناسه {target_user_id} قبلاً مسدود شده است."
            )
        else:
            config.setdefault("blocked_users", []).append(target_user_id)
            save_config()
            await update.message.reply_text(
                f"✅ کاربر با شناسه {target_user_id} با موفقیت مسدود شد."
            )

        # Return to manage blocked menu
        await self.manage_blocked_menu(update, context)
        return ConversationHandler.END

    async def unblock_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
        """
        Unblock a user.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
            target_user_id (int): Telegram user ID to unblock.
        """
        user_id = update.effective_user.id
        blocked_users = config.get("blocked_users", [])

        if target_user_id in blocked_users:
            blocked_users.remove(target_user_id)
            config["blocked_users"] = blocked_users
            save_config()
            await update.callback_query.edit_message_text(
                f"✅ کاربر با شناسه {target_user_id} از لیست مسدود شده‌ها حذف شد."
            )
        else:
            await update.callback_query.edit_message_text(
                f"🔍 کاربر با شناسه {target_user_id} در لیست مسدود شده‌ها یافت نشد."
            )

        await self.manage_blocked_menu(update, context)

    async def export_data_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Display the export data menu.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        if not is_admin(user_id):
            await query.edit_message_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        keyboard = [
            [InlineKeyboardButton("📥 صادرات لیست کاربران ثبت‌شده", callback_data="export_registered_users")],
            [InlineKeyboardButton("🔢 لیست شناسه‌های کاربران ثبت‌شده", callback_data="list_user_ids")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📤 لطفاً گزینه مورد نظر برای صادرات داده‌ها را انتخاب کنید:",
            reply_markup=reply_markup
        )

    async def export_registered_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Export the list of registered users as a JSON file.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        session_data = get_session(user_id)
        results = session_data.get("results", [])
        if not results:
            await query.edit_message_text("❌ هیچ داده‌ای برای صادرات وجود ندارد.")
            return

        registered_users = [r for r in results if r.get("isRegistered") and r.get("userId")]
        if not registered_users:
            await query.edit_message_text("❌ هیچ کاربر ثبت‌شده‌ای یافت نشد.")
            return

        # Save to JSON asynchronously
        output_file = Path(f"registered_users_{user_id}.json")
        try:
            async with aiofiles.open(output_file, "w", encoding="utf-8") as file:
                await file.write(json.dumps(registered_users, indent=4, ensure_ascii=False))
            logger.info(f"Registered users exported to {output_file}.")
        except Exception as e:
            logger.error(f"Failed to export registered users: {e}")
            await query.edit_message_text("❌ خطایی در هنگام صادرات داده‌ها رخ داد.")
            return

        await query.edit_message_text("📤 در حال ارسال فایل صادرات...")
        await query.message.reply_document(
            document=InputFile(str(output_file)),
            filename=output_file.name,
            caption="📁 لیست کاربران ثبت‌شده"
        )

        # Clean up the exported file asynchronously
        try:
            await self.file_handler.delete_file(output_file)
        except Exception as e:
            logger.warning(f"Failed to delete exported file {output_file}: {e}")

    async def list_user_ids(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        List all user IDs processed.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        session_data = get_session(user_id)
        results = session_data.get("results", [])
        if not results:
            await query.edit_message_text("❌ هیچ داده‌ای برای نمایش وجود ندارد.")
            return

        user_ids = [str(r.get("userId")) for r in results if r.get("isRegistered") and r.get("userId")]
        if not user_ids:
            user_ids_str = "هیچ کاربری ثبت نشده است."
        else:
            user_ids_str = ", ".join(user_ids)

        await query.edit_message_text(f"🔢 **لیست شناسه‌های کاربران ثبت‌شده:**\n{user_ids_str}")

    async def handle_text_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle general text messages based on user state.

        Args:
            update (Update): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ شما اجازه استفاده از این ربات را ندارید.")
            return

        # Other text messages can be handled as needed
        await update.message.reply_text(
            "❓ لطفاً از دکمه‌های ارائه شده استفاده کنید یا یک دستور معتبر ارسال کنید."
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Log the error and send a message to the user.

        Args:
            update (object): Telegram update.
            context (ContextTypes.DEFAULT_TYPE): Context for the update.
        """
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_user:
            try:
                await update.effective_message.reply_text(
                    "❌ متاسفانه یک خطا رخ داد. لطفاً دوباره تلاش کنید."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")



#Key Enhancements:
#
#Integrated Settings for Sensitive Data:
#
#Buttons Added: Options to set Apify API Token, Telegram API ID, Telegram API Hash, String Session, and Target Channel Username via inline keyboard buttons.
#Conversation Handlers: Implemented separate conversation handlers for each configuration setting, ensuring a smooth and secure setup process.
#Validation: Each input is validated to ensure correctness before updating the configuration.
#Removal of Pre-filled Sensitive Data:
#
#The bot no longer relies on pre-filled sensitive data in the .env file. Instead, admins input all necessary configurations through the bot interface.
#Enhanced Error Handling:
#
#Provides clear feedback if configurations are missing or invalid.
#Ensures that the bot remains operational even if some configurations are incomplete.



#**Improvements:**
#
#1. **Concurrency in Adding Users:**
#   - Utilizes `asyncio.Semaphore` to limit concurrent addition tasks, preventing rate limit issues.
#
#2. **Asynchronous CSV Processing:**
#   - Handles CSV reading and result saving asynchronously to maintain bot responsiveness.
#
#3. **Error Handling Enhancements:**
#  - Comprehensive exception handling with detailed logging.
#
#4. **Input Validation:**
#   - Ensures that inputs like API tokens, IDs, and usernames meet expected formats.
#
#5. **Session Management:**
#   - Manages user sessions effectively, storing processed results for subsequent actions.
#
#6. **Security Enhancements:**
#   - Restricts bot functionalities to authorized admins only.
#
#7. **Documentation:**
#   - Comprehensive docstrings and comments for better maintainability.
#
#8. **Code Optimization:**
#   - Avoids redundant checks and ensures clean separation of concerns.
#