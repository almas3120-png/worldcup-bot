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
    @dp.message(Registration.mobile)
async def get_mobile(
        message: types.Message,
        state: FSMContext
):

    if not message.contact:

        await message.answer(
            "لطفاً از دکمه ارسال شماره موبایل استفاده کنید."
        )
        return

    await state.update_data(
        mobile=message.contact.phone_number
    )

    await message.answer(
        "استان محل سکونت را وارد کنید:"
    )

    await state.set_state(
        Registration.province
    )
    @dp.message(Registration.rules)
async def accept_rules(
        message: types.Message,
        state: FSMContext
):

    if message.text != "✅ قوانین را می‌پذیرم":

        await message.answer(
            "برای ادامه باید قوانین را بپذیرید."
        )
        return

    data = await state.get_data()

    cur.execute("""
    INSERT OR REPLACE INTO users(
        user_id,
        username,
        first_name,
        last_name,
        national_code,
        mobile,
        province,
        city,
        points,
        registered
    )
    VALUES(?,?,?,?,?,?,?,?,?,?)
    """, (
        message.from_user.id,
        message.from_user.username or "",
        data["first_name"],
        data["last_name"],
        data["national_code"],
        data["mobile"],
        data["province"],
        data["city"],
        0,
        1
    ))

    db.commit()

    await state.clear()

    await message.answer(
        "✅ ثبت نام شما با موفقیت انجام شد.\n\n"
        "به سامانه پیش‌بینی جام جهانی 2026 با هنگویه اسپورت خوش آمدید.",
        reply_markup=main_menu
    )
    @dp.message(F.text == "🎁 جوایز")
async def prizes(message: types.Message):

    await message.answer(
        "🎁 جوایز مسابقه پیش‌بینی جام جهانی 2026\n\n"

        "🥇 نفر اول\n"
        "100,000,000 ریال\n\n"

        "🥈 نفر دوم\n"
        "50,000,000 ریال\n\n"

        "🥉 نفر سوم\n"
        "25,000,000 ریال\n\n"

        "🏅 نفرات چهارم تا دهم\n"
        "هر نفر 10,000,000 ریال\n\n"

        "🏆 با هنگویه اسپورت"
    )
    @dp.message(F.text == "👤 رتبه من")
async def my_rank(message: types.Message):

    if not is_registered(
            message.from_user.id):
        return

    row = cur.execute("""
    SELECT points
    FROM users
    WHERE user_id=?
    """, (
        message.from_user.id,
    )).fetchone()

    points = row[0] if row else 0

    await message.answer(
        f"🏅 امتیاز شما: {points}"
    )
    @dp.message(F.text == "🥇 نفرات برتر")
async def top_users(message: types.Message):

    rows = cur.execute("""
    SELECT first_name,
           last_name,
           points
    FROM users
    ORDER BY points DESC
    LIMIT 10
    """).fetchall()

    if not rows:

        await message.answer(
            "هنوز رتبه‌بندی ایجاد نشده است."
        )
        return

    text = "🏆 10 نفر برتر\n\n"

    for i, row in enumerate(rows, start=1):

        text += (
            f"{i}- "
            f"{row[0]} "
            f"{row[1]} "
            f"({row[2]} امتیاز)\n"
        )

    await message.answer(text)
    @dp.message(F.text == "📋 مسابقات")
async def show_matches(message: types.Message):

    rows = cur.execute("""
    SELECT id,
           team1,
           team2,
           match_date,
           finished
    FROM matches
    ORDER BY id DESC
    LIMIT 6
    """).fetchall()

    if not rows:

        await message.answer(
            "هنوز مسابقه‌ای ثبت نشده است."
        )
        return

    text = "📋 مسابقات فعال\n\n"

    for row in rows:

        status = (
            "✅ پایان یافته"
            if row[4] else
            "⏳ در انتظار پیش‌بینی"
        )

        text += (
            f"شناسه: {row[0]}\n"
            f"{row[1]} 🆚 {row[2]}\n"
            f"📅 {row[3]}\n"
            f"{status}\n\n"
        )

    await message.answer(text)
    predict_match = State()
    class Registration(StatesGroup):

    first_name = State()
    last_name = State()
    national_code = State()
    mobile = State()
    province = State()
    city = State()
    rules = State()

    predict_match = State()
    @dp.message(F.text == "🏆 شرکت در مسابقه")
async def participate(
        message: types.Message,
        state: FSMContext
):

    rows = cur.execute("""
    SELECT id,
           team1,
           team2
    FROM matches
    WHERE finished=0
    ORDER BY id DESC
    LIMIT 6
    """).fetchall()

    if not rows:

        await message.answer(
            "در حال حاضر مسابقه فعالی وجود ندارد."
        )
        return

    text = (
        "شناسه مسابقه را همراه نتیجه وارد کنید.\n\n"
        "مثال:\n"
        "1 2-1\n\n"
    )

    for row in rows:

        text += (
            f"{row[0]} ➜ "
            f"{row[1]} vs {row[2]}\n"
        )

    await message.answer(text)

    await state.set_state(
        Registration.predict_match
    )
    @dp.message(Registration.predict_match)
async def save_prediction(
        message: types.Message,
        state: FSMContext
):

    try:

        match_id, score = (
            message.text.split()
        )

        pred1, pred2 = map(
            int,
            score.split("-")
        )

        match_id = int(match_id)

    except:

        await message.answer(
            "فرمت صحیح:\n"
            "1 2-1"
        )
        return

    match = cur.execute("""
    SELECT id
    FROM matches
    WHERE id=?
    AND finished=0
    """, (
        match_id,
    )).fetchone()

    if not match:

        await message.answer(
            "مسابقه معتبر نیست."
        )
        return

    cur.execute("""
    INSERT OR REPLACE INTO predictions(
        user_id,
        match_id,
        pred1,
        pred2
    )
    VALUES(?,?,?,?)
    """, (

        message.from_user.id,
        match_id,
        pred1,
        pred2

    ))

    db.commit()

    await state.clear()

    await message.answer(
        "✅ پیش‌بینی شما ثبت شد.",
        reply_markup=main_menu
    )
    ADMIN_ID = 1562540
    @dp.message(Command("addmatch"))
async def add_match(
        message: types.Message
):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        data = message.text.replace(
            "/addmatch ",
            ""
        )

        team1, team2, date = data.split("|")

    except:

        await message.answer(
            "/addmatch ایران|برزیل|2026-06-15"
        )
        return

    active_count = cur.execute("""
    SELECT COUNT(*)
    FROM matches
    WHERE finished=0
    """).fetchone()[0]

    if active_count >= 6:

        await message.answer(
            "حداکثر 6 مسابقه فعال مجاز است."
        )
        return

    cur.execute("""
    INSERT INTO matches(
        team1,
        team2,
        match_date
    )
    VALUES(?,?,?)
    """, (
        team1,
        team2,
        date
    ))

    db.commit()

    await message.answer(
        "✅ مسابقه ثبت شد."
    )
    /addmatch ایران|برزیل|2026-06-15

/addmatch آلمان|فرانسه|2026-06-16

/addmatch آرژانتین|اسپانیا|2026-06-17
@dp.message(Command("result"))
async def set_result(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        _, match_id, score = message.text.split()

        s1, s2 = map(
            int,
            score.split("-")
        )

        match_id = int(match_id)

    except:

        await message.answer(
            "/result 1 2-1"
        )
        return

    cur.execute("""
    UPDATE matches
    SET score1=?,
        score2=?,
        finished=1
    WHERE id=?
    """, (
        s1,
        s2,
        match_id
    ))

    db.commit()

    await calculate_points(
        match_id,
        s1,
        s2
    )

    await message.answer(
        "✅ نتیجه ثبت شد و امتیازات محاسبه گردید."
    )
    async def calculate_points(
        match_id,
        real1,
        real2
):

    preds = cur.execute("""
    SELECT user_id,
           pred1,
           pred2
    FROM predictions
    WHERE match_id=?
    """, (
        match_id,
    )).fetchall()

    for user_id, pred1, pred2 in preds:

        points = 0

        # نتیجه دقیق
        if pred1 == real1 and pred2 == real2:

            points = 20

        else:

            # مساوی
            if pred1 == pred2 and real1 == real2:

                points = 13

            else:

                pred_diff = pred1 - pred2
                real_diff = real1 - real2

                pred_winner = (
                    1 if pred_diff > 0
                    else 2 if pred_diff < 0
                    else 0
                )

                real_winner = (
                    1 if real_diff > 0
                    else 2 if real_diff < 0
                    else 0
                )

                if pred_winner == real_winner:

                    if pred_diff == real_diff:

                        points = 13

                    else:

                        points = 8

        cur.execute("""
        UPDATE users
        SET points = points + ?
        WHERE user_id=?
        """, (
            points,
            user_id
        ))

    db.commit()
    ایران 2 - 1 برزیل
    2 - 1
    20
    3 - 2
    13
    1 - 0
    8
    2 - 2
    1 - 1
    13
    @dp.message(Command("users"))
async def users_count(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    count = cur.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE registered=1
    """).fetchone()[0]

    await message.answer(
        f"👥 تعداد کاربران ثبت نام شده: {count}"
    )
    @dp.message(Command("top"))
async def admin_top(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    rows = cur.execute("""
    SELECT first_name,
           last_name,
           points
    FROM users
    ORDER BY points DESC
    LIMIT 10
    """).fetchall()

    text = "🏆 رتبه بندی فعلی\n\n"

    for i, row in enumerate(rows, start=1):

        text += (
            f"{i}. "
            f"{row[0]} "
            f"{row[1]} "
            f"- "
            f"{row[2]} امتیاز\n"
        )

    await message.answer(text)
    admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ افزودن مسابقه"),
            KeyboardButton(text="🏁 ثبت نتیجه")
        ],
        [
            KeyboardButton(text="📢 پیام همگانی"),
            KeyboardButton(text="👥 آمار کاربران")
        ],
        [
            KeyboardButton(text="🏆 رتبه بندی")
        ]
    ],
    resize_keyboard=True
)@dp.message(Command("admin"))
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🔐 پنل مدیریت",
        reply_markup=admin_menu
    )@dp.message(F.text == "👥 آمار کاربران")
async def users_stats(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    users = cur.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE registered=1
    """).fetchone()[0]

    predictions = cur.execute("""
    SELECT COUNT(*)
    FROM predictions
    """).fetchone()[0]

    await message.answer(
        f"👥 کاربران: {users}\n"
        f"⚽ تعداد پیش‌بینی‌ها: {predictions}"
    )broadcast = State()broadcast = State()@dp.message(F.text == "📢 پیام همگانی")
async def start_broadcast(
        message: types.Message,
        state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "متن پیام را ارسال کنید:"
    )

    await state.set_state(
        Registration.broadcast
    )@dp.message(Registration.broadcast)
async def send_broadcast(
        message: types.Message,
        state: FSMContext
):

    users = cur.execute("""
    SELECT user_id
    FROM users
    WHERE registered=1
    """).fetchall()

    sent = 0

    for user in users:

        try:

            await bot.send_message(
                user[0],
                message.text
            )

            sent += 1

        except:
            pass

    await state.clear()

    await message.answer(
        f"✅ پیام برای {sent} نفر ارسال شد."
    )welcome_text = """
🏆 پیش‌بینی جام جهانی 2026
با هنگویه اسپورت

به بزرگ‌ترین مسابقه پیش‌بینی فوتبال خوش آمدید.

🎯 پیش‌بینی نتایج
🏅 کسب امتیاز
🏆 رقابت با سایر شرکت‌کنندگان
🎁 دریافت جوایز نقدی

برای ادامه ابتدا ثبت نام خود را تکمیل نمایید.
"""prize_text = """
🎁 جوایز مسابقه

🥇 نفر اول
100 میلیون ریال

🥈 نفر دوم
50 میلیون ریال

🥉 نفر سوم
25 میلیون ریال

🏅 نفرات چهارم تا دهم
هر نفر 10 میلیون ریال
"""from datetime import datetime
/addmatch ایران|برزیل|2026-06-15 18:00
match = cur.execute("""
SELECT match_date
FROM matches
WHERE id=?
""",(match_id,)).fetchone()

match_time = datetime.strptime(
    match[0],
    "%Y-%m-%d %H:%M"
)

if datetime.now() >= match_time:
    await message.answer(
        "⛔ زمان ثبت پیش‌بینی این مسابقه به پایان رسیده است."
    )
    return
    @dp.message(F.text == "👤 رتبه من")
async def my_rank(message: types.Message):

    users = cur.execute("""
    SELECT user_id, points
    FROM users
    ORDER BY points DESC
    """).fetchall()

    rank = 0

    for i, user in enumerate(users, start=1):

        if user[0] == message.from_user.id:
            rank = i
            points = user[1]
            break

    await message.answer(
        f"🏅 رتبه شما: {rank}\n"
        f"⭐ امتیاز شما: {points}"
    )
    KeyboardButton(text="👥 شرکت‌کنندگان")
    @dp.message(F.text == "👥 شرکت‌کنندگان")
async def participants(message: types.Message):

    count = cur.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE registered=1
    """).fetchone()[0]

    await message.answer(
        f"👥 تعداد شرکت‌کنندگان: {count}"
    )
    @dp.message(F.text == "🥇 نفرات برتر")
async def top_users(message: types.Message):

    rows = cur.execute("""
    SELECT first_name,
           last_name,
           points
    FROM users
    ORDER BY points DESC
    LIMIT 10
    """).fetchall()

    text = "🏆 ده نفر برتر مسابقات\n\n"

    medals = [
        "🥇","🥈","🥉",
        "4️⃣","5️⃣","6️⃣",
        "7️⃣","8️⃣","9️⃣","🔟"
    ]

    for i,row in enumerate(rows):

        text += (
            f"{medals[i]} "
            f"{row[0]} {row[1]}\n"
            f"⭐ {row[2]} امتیاز\n\n"
        )

    await message.answer(text)
    @dp.message(Command("deletematch"))
async def delete_match(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, match_id = message.text.split()
        match_id = int(match_id)
    except:
        await message.answer(
            "/deletematch 1"
        )
        return

    cur.execute(
        "DELETE FROM matches WHERE id=?",
        (match_id,)
    )

    db.commit()

    await message.answer(
        "✅ مسابقه حذف شد."
    )
    @dp.message(Command("editresult"))
async def edit_result(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        _, match_id, score = message.text.split()

        s1, s2 = map(
            int,
            score.split("-")
        )

    except:

        await message.answer(
            "/editresult 1 2-1"
        )
        return

    cur.execute("""
    UPDATE matches
    SET score1=?,
        score2=?
    WHERE id=?
    """,(s1,s2,match_id))

    db.commit()

    await message.answer(
        "✅ نتیجه ویرایش شد."
    )
    await message.answer(
"""
✅ ثبت نام شما تکمیل شد.

🏆 پیش‌بینی جام جهانی 2026
با هنگویه اسپورت

اکنون می‌توانید از منوی اصلی
در مسابقات شرکت کنید.

🎁 جوایز نقدی برای 10 نفر برتر
در نظر گرفته شده است.

موفق باشید.
""",
reply_markup=main_menu
)
    
