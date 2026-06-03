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
)

# =====================================
# SETTINGS
# =====================================

TOKEN = "8611001244:AAHSlm857J7_eThnFHwO_bVMutU2dj3rMrw"
ADMIN_ID = 1562540

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =====================================
# DATABASE
# =====================================

db = sqlite3.connect(
    "worldcup.db",
    check_same_thread=False
)

cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    national_code TEXT,
    mobile TEXT,
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

# =====================================
# FSM
# =====================================

class Registration(StatesGroup):

    full_name = State()
    national_code = State()
    mobile = State()
    rules = State()

# =====================================
# HELPERS
# =====================================

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
    # =====================================
# MENUS
# =====================================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🏆 شرکت در مسابقه"
            ),
            KeyboardButton(
                text="⚽ مسابقات"
            )
        ],
        [
            KeyboardButton(
                text="🥇 نفرات برتر"
            ),
            KeyboardButton(
                text="👤 رتبه من"
            )
        ],
        [
            KeyboardButton(
                text="🎁 جوایز"
            )
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
                text="✅ قوانین تأیید شد"
            )
        ]
    ],
    resize_keyboard=True
)

RULES_TEXT = """
🏆 قوانین مسابقه پیش بینی جام جهانی 2026

1- هر شخص فقط یک حساب کاربری مجاز دارد.

2- اطلاعات ثبت شده باید صحیح باشد.

3- پس از ثبت نام امکان تغییر اطلاعات وجود ندارد.

4- تصمیم نهایی برگزار کننده معتبر است.

5- شرکت در مسابقه به منزله پذیرش قوانین است.
"""

PRIZES_TEXT = """
🎁 جوایز مسابقه

🥇 نفر اول
100 میلیون ریال

🥈 نفر دوم
50 میلیون ریال

🥉 نفر سوم
25 میلیون ریال

🏅 نفرات چهارم تا دهم

هر نفر 10 میلیون ریال
"""
# =====================================
# REGISTRATION
# =====================================

@dp.message(Command("start"))
async def start(
    message: types.Message,
    state: FSMContext
):

    if is_registered(
        message.from_user.id
    ):

        await message.answer(
            "🏆 به سامانه پیش‌بینی جام جهانی 2026 با هنگویه اسپورت خوش آمدید.",
            reply_markup=main_menu
        )

        return

    await message.answer(
        "لطفاً نام و نام خانوادگی خود را وارد کنید:"
    )

    await state.set_state(
        Registration.full_name
    )


@dp.message(Registration.full_name)
async def get_full_name(
    message: types.Message,
    state: FSMContext
):

    full_name = message.text.strip()

    if len(full_name) < 5:

        await message.answer(
            "نام و نام خانوادگی معتبر وارد کنید."
        )

        return

    await state.update_data(
        full_name=full_name
    )

    await message.answer(
        "کد ملی 10 رقمی خود را وارد کنید:"
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

    if not code.isdigit():

        await message.answer(
            "کد ملی فقط باید عدد باشد."
        )

        return

    if len(code) != 10:

        await message.answer(
            "کد ملی باید 10 رقم باشد."
        )

        return

    await state.update_data(
        national_code=code
    )

    await message.answer(
        "شماره موبایل خود را ارسال کنید:",
        reply_markup=contact_keyboard
    )

    await state.set_state(
        Registration.mobile
    )


@dp.message(
    Registration.mobile,
    F.contact
)
async def get_mobile(
    message: types.Message,
    state: FSMContext
):

    mobile = (
        message.contact.phone_number
    )

    if mobile.startswith("+98"):

        mobile = (
            "0" + mobile[3:]
        )

    await state.update_data(
        mobile=mobile
    )

    await message.answer(
        RULES_TEXT,
        reply_markup=rules_keyboard
    )

    await state.set_state(
        Registration.rules
    )
    # =====================================
# COMPLETE REGISTRATION
# =====================================

@dp.message(
    Registration.rules,
    F.text == "✅ قوانین تأیید شد"
)
async def finish_registration(
    message: types.Message,
    state: FSMContext
):

    data = await state.get_data()

    cur.execute(
        """
        INSERT OR REPLACE INTO users(
            user_id,
            username,
            full_name,
            national_code,
            mobile,
            registered
        )
        VALUES(?,?,?,?,?,1)
        """,
        (
            message.from_user.id,
            message.from_user.username or "",
            data["full_name"],
            data["national_code"],
            data["mobile"]
        )
    )

    db.commit()

    await state.clear()

    await message.answer(
        "✅ ثبت نام شما با موفقیت انجام شد.\n\n"
        "به مسابقه پیش‌بینی جام جهانی 2026 خوش آمدید.",
        reply_markup=main_menu
    )

# =====================================
# PRIZES
# =====================================

@dp.message(F.text == "🎁 جوایز")
async def prizes(
    message: types.Message
):

    await message.answer(
        PRIZES_TEXT
    )

# =====================================
# MY RANK
# =====================================

@dp.message(F.text == "👤 رتبه من")
async def my_rank(
    message: types.Message
):

    row = cur.execute(
        """
        SELECT points
        FROM users
        WHERE user_id=?
        """,
        (message.from_user.id,)
    ).fetchone()

    if not row:

        return

    my_points = row[0]

    rank = cur.execute(
        """
        SELECT COUNT(*) + 1
        FROM users
        WHERE points > ?
        """,
        (my_points,)
    ).fetchone()[0]

    await message.answer(
        f"🏅 رتبه شما: {rank}\n"
        f"⭐ امتیاز شما: {my_points}"
    )

# =====================================
# TOP PLAYERS
# =====================================

@dp.message(F.text == "🥇 نفرات برتر")
async def top_players(
    message: types.Message
):

    rows = cur.execute(
        """
        SELECT full_name, points
        FROM users
        ORDER BY points DESC
        LIMIT 10
        """
    ).fetchall()

    if not rows:

        await message.answer(
            "هنوز رتبه‌بندی تشکیل نشده است."
        )
        return

    text = "🏆 10 نفر برتر مسابقه\n\n"

    counter = 1

    for name, points in rows:

        text += (
            f"{counter}. "
            f"{name} - "
            f"{points} امتیاز\n"
        )

        counter += 1

    await message.answer(text)
    # =====================================
# MATCHES
# =====================================

@dp.message(F.text == "⚽ مسابقات")
async def show_matches(
    message: types.Message
):

    rows = cur.execute(
        """
        SELECT
            id,
            team1,
            team2,
            match_date,
            finished
        FROM matches
        ORDER BY id DESC
        """
    ).fetchall()

    if not rows:

        await message.answer(
            "هنوز مسابقه‌ای ثبت نشده است."
        )

        return

    text = "⚽ مسابقات فعال\n\n"

    for row in rows:

        match_id = row[0]
        team1 = row[1]
        team2 = row[2]
        date = row[3]
        finished = row[4]

        status = (
            "✅ پایان یافته"
            if finished
            else "⏳ باز"
        )

        text += (
            f"🆔 {match_id}\n"
            f"{team1} 🆚 {team2}\n"
            f"📅 {date}\n"
            f"{status}\n\n"
        )

    text += (
        "برای ثبت پیش‌بینی:\n"
        "/predict شناسه نتیجه\n\n"
        "مثال:\n"
        "/predict 1 2-1"
    )

    await message.answer(text)

# =====================================
# PREDICT
# =====================================

@dp.message(Command("predict"))
async def predict_match(
    message: types.Message
):

    if not is_registered(
        message.from_user.id
    ):
        return

    try:

        parts = message.text.split()

        match_id = int(parts[1])

        score = parts[2]

        pred1 = int(
            score.split("-")[0]
        )

        pred2 = int(
            score.split("-")[1]
        )

    except:

        await message.answer(
            "فرمت صحیح:\n"
            "/predict 1 2-1"
        )

        return

    match = cur.execute(
        """
        SELECT finished
        FROM matches
        WHERE id=?
        """,
        (match_id,)
    ).fetchone()

    if not match:

        await message.answer(
            "شناسه مسابقه نامعتبر است."
        )

        return

    if match[0] == 1:

        await message.answer(
            "این مسابقه پایان یافته است."
        )

        return

    cur.execute(
        """
        INSERT OR REPLACE INTO predictions(
            user_id,
            match_id,
            pred1,
            pred2
        )
        VALUES(?,?,?,?)
        """,
        (
            message.from_user.id,
            match_id,
            pred1,
            pred2
        )
    )

    db.commit()

    await message.answer(
        f"✅ پیش‌بینی شما ثبت شد\n\n"
        f"نتیجه انتخابی:\n"
        f"{pred1} - {pred2}"
    )
    # =====================================
# POINTS CALCULATOR
# =====================================

async def calculate_points(
    match_id,
    real1,
    real2
):

    predictions = cur.execute(
        """
        SELECT
            user_id,
            pred1,
            pred2
        FROM predictions
        WHERE match_id=?
        """,
        (match_id,)
    ).fetchall()

    for user_id, pred1, pred2 in predictions:

        points = 0

        # نتیجه دقیق
        if pred1 == real1 and pred2 == real2:

            points = 20

        else:

            real_diff = real1 - real2
            pred_diff = pred1 - pred2

            # مساوی
            if real1 == real2 and pred1 == pred2:

                points = 13

            # برد تیم اول
            elif real1 > real2 and pred1 > pred2:

                if real_diff == pred_diff:
                    points = 13
                else:
                    points = 8

            # برد تیم دوم
            elif real2 > real1 and pred2 > pred1:

                if real_diff == pred_diff:
                    points = 13
                else:
                    points = 8

        cur.execute(
            """
            UPDATE users
            SET points = points + ?
            WHERE user_id=?
            """,
            (
                points,
                user_id
            )
        )

    db.commit()

# =====================================
# ADMIN - ADD MATCH
# =====================================

@dp.message(Command("addmatch"))
async def add_match(
    message: types.Message
):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        data = (
            message.text.replace(
                "/addmatch ",
                ""
            )
        )

        team1, team2, match_date = (
            data.split("|")
        )

    except:

        await message.answer(
            "نمونه:\n"
            "/addmatch ایران|برزیل|2026-06-15 18:00"
        )

        return

    active_count = cur.execute(
        """
        SELECT COUNT(*)
        FROM matches
        WHERE finished=0
        """
    ).fetchone()[0]

    if active_count >= 6:

        await message.answer(
            "حداکثر 6 مسابقه فعال مجاز است."
        )

        return

    cur.execute(
        """
        INSERT INTO matches(
            team1,
            team2,
            match_date
        )
        VALUES(?,?,?)
        """,
        (
            team1,
            team2,
            match_date
        )
    )

    db.commit()

    await message.answer(
        "✅ مسابقه ثبت شد."
    )

# =====================================
# ADMIN - RESULT
# =====================================

@dp.message(Command("result"))
async def set_result(
    message: types.Message
):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        parts = message.text.split()

        match_id = int(parts[1])

        score = parts[2]

        real1 = int(
            score.split("-")[0]
        )

        real2 = int(
            score.split("-")[1]
        )

    except:

        await message.answer(
            "نمونه:\n"
            "/result 1 2-1"
        )

        return

    cur.execute(
        """
        UPDATE matches
        SET
            score1=?,
            score2=?,
            finished=1
        WHERE id=?
        """,
        (
            real1,
            real2,
            match_id
        )
    )

    db.commit()

    await calculate_points(
        match_id,
        real1,
        real2
    )

    await message.answer(
        "✅ نتیجه ثبت شد و امتیازات محاسبه گردید."
    )
    # =====================================
# ADMIN - USERS COUNT
# =====================================

@dp.message(Command("users"))
async def users_count(
    message: types.Message
):

    if message.from_user.id != ADMIN_ID:
        return

    total = cur.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE registered=1
        """
    ).fetchone()[0]

    await message.answer(
        f"👥 تعداد کاربران ثبت نام شده:\n{total}"
    )

# =====================================
# ADMIN - USER INFO
# =====================================

@dp.message(Command("userinfo"))
async def user_info(
    message: types.Message
):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        user_id = int(
            message.text.split()[1]
        )

    except:

        await message.answer(
            "/userinfo USER_ID"
        )

        return

    row = cur.execute(
        """
        SELECT
            full_name,
            national_code,
            mobile,
            points
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()

    if not row:

        await message.answer(
            "کاربر پیدا نشد."
        )

        return

    text = (
        f"👤 نام:\n{row[0]}\n\n"
        f"🆔 کد ملی:\n{row[1]}\n\n"
        f"📱 موبایل:\n{row[2]}\n\n"
        f"⭐ امتیاز:\n{row[3]}"
    )

    await message.answer(text)

# =====================================
# ADMIN - EDIT MOBILE
# =====================================

@dp.message(Command("editmobile"))
async def edit_mobile(
    message: types.Message
):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        parts = message.text.split()

        user_id = int(parts[1])

        new_mobile = parts[2]

    except:

        await message.answer(
            "/editmobile USER_ID MOBILE"
        )

        return

    cur.execute(
        """
        UPDATE users
        SET mobile=?
        WHERE user_id=?
        """,
        (
            new_mobile,
            user_id
        )
    )

    db.commit()

    await message.answer(
        "✅ شماره موبایل بروزرسانی شد."
    )

# =====================================
# ADMIN COMMANDS HELP
# =====================================

@dp.message(Command("admin"))
async def admin_panel(
    message: types.Message
):

    if message.from_user.id != ADMIN_ID:1562540
        return

    text = """
👑 پنل مدیریت

➕ افزودن مسابقه:
/addmatch ایران|برزیل|2026-06-15 18:00

🏁 ثبت نتیجه:
/result 1 2-1

👥 تعداد کاربران:
/users

🔎 اطلاعات کاربر:
/userinfo USER_ID

📱 تغییر موبایل:
/editmobile USER_ID MOBILE
"""

    await message.answer(text)

# =====================================
# MAIN
# =====================================

async def main():

    print("World Cup Bot Started")

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
