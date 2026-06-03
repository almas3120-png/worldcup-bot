import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 1562540

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = sqlite3.connect("worldcup.db")
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    national_code TEXT,
    mobile TEXT,
    province TEXT,
    city TEXT,
    points INTEGER DEFAULT 0,
    registered INTEGER DEFAULT 0
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS matches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team1 TEXT,
    team2 TEXT,
    match_date TEXT,
    score1 INTEGER,
    score2 INTEGER,
    finished INTEGER DEFAULT 0
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS predictions(
    user_id INTEGER,
    match_id INTEGER,
    pred1 INTEGER,
    pred2 INTEGER,
    PRIMARY KEY(user_id, match_id)
)
""")

db.commit()
class Registration(StatesGroup):
    first_name = State()
    last_name = State()
    national_code = State()
    mobile = State()
    province = State()
    city = State()
    rules = State()
    main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏆 شرکت در مسابقه"),
            KeyboardButton(text="📋 مسابقات")
        ],
        [
            KeyboardButton(text="🥇 نفرات برتر"),
            KeyboardButton(text="👤 رتبه من")
        ],
        [
            KeyboardButton(text="🎁 جوایز")
        ]
    ],
    resize_keyboard=True
)
    contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 ارسال شماره موبایل",
                request_contact=True
            )
        ]
    ],
    resize_keyboard=True
)
    rules_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="✅ قوانین را می‌پذیرم"
            )
        ]
    ],
    resize_keyboard=True
)
    def is_registered(user_id):

    row = cur.execute(
        """
        SELECT registered
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()

    return row and row[0] == 1
    @dp.message(Command("start"))
async def start(
        message: types.Message,
        state: FSMContext
):

    if is_registered(message.from_user.id):

        await message.answer(
            "🏆 به سامانه پیش‌بینی جام جهانی 2026 با هنگویه اسپورت خوش آمدید.",
            reply_markup=main_menu
        )

        return

    await message.answer(
        "نام خود را وارد کنید:"
    )

    await state.set_state(
        Registration.first_name
    )
    @dp.message(Command("start"))
async def start(
        message: types.Message,
        state: FSMContext
):

    if is_registered(message.from_user.id):

        await message.answer(
            "🏆 به سامانه پیش‌بینی جام جهانی 2026 با هنگویه اسپورت خوش آمدید.",
            reply_markup=main_menu
        )

        return

    await message.answer(
        "نام خود را وارد کنید:"
    )

    await state.set_state(
        Registration.first_name
    )
    @dp.message(Registration.first_name)
async def get_first_name(
        message: types.Message,
        state: FSMContext
):

    await state.update_data(
        first_name=message.text
    )

    await message.answer(
        "نام خانوادگی را وارد کنید:"
    )

    await state.set_state(
        Registration.last_name
    )
    @dp.message(Registration.last_name)
async def get_last_name(
        message: types.Message,
        state: FSMContext
):

    await state.update_data(
        last_name=message.text
    )

    await message.answer(
        "کد ملی 10 رقمی را وارد کنید:"
    )

    await state.set_state(
        Registration.national_code
    )
    @dp.message(Registration.national_code)
async def get_national_code(
        message: types.Message,
        state: FSMContext
):

    code = message.text.strip()

    if not code.isdigit() or len(code) != 10:

        await message.answer(
            "کد ملی نامعتبر است."
        )
        return

    await state.update_data(
        national_code=code
    )

    await message.answer(
        "شماره موبایل را ارسال کنید:",
        reply_markup=contact_keyboard
    )

    await state.set_state(
        Registration.mobile
    )
    
