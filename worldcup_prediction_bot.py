import os
import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Railway Variables
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise ValueError("BOT_TOKEN not found!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Database
db = sqlite3.connect("worldcup.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS matches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team1 TEXT,
    team2 TEXT,
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


def register_user(user):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id, username) VALUES (?, ?)",
        (user.id, user.username or "")
    )
    db.commit()


@dp.message(Command("start"))
async def start(message: types.Message):
    register_user(message.from_user)

    await message.answer(
        "🏆 ربات پیش‌بینی جام جهانی\n\n"
        "/matches - لیست مسابقات\n"
        "/predict 1 2-1 - ثبت پیش‌بینی\n"
        "/ranking - جدول رتبه‌بندی"
    )


@dp.message(Command("matches"))
async def matches(message: types.Message):

    rows = cur.execute(
        "SELECT id, team1, team2, finished FROM matches"
    ).fetchall()

    if not rows:
        await message.answer("هیچ مسابقه‌ای ثبت نشده است.")
        return

    text = "📋 مسابقات:\n\n"

    for row in rows:
        status = "✅ تمام شده" if row[3] else "⏳ باز"

        text += (
            f"ID:{row[0]}\n"
            f"{row[1]} vs {row[2]}\n"
            f"{status}\n\n"
        )

    await message.answer(text)


@dp.message(Command("predict"))
async def predict(message: types.Message):

    register_user(message.from_user)

    try:
        _, match_id, score = message.text.split()

        p1, p2 = map(int, score.split("-"))
        match_id = int(match_id)

    except:
        await message.answer(
            "نمونه:\n/predict 1 2-1"
        )
        return

    match = cur.execute(
        "SELECT finished FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if not match:
        await message.answer("شناسه مسابقه معتبر نیست.")
        return

    if match[0] == 1:
        await message.answer("مسابقه تمام شده است.")
        return

    cur.execute("""
    INSERT OR REPLACE INTO predictions
    (user_id, match_id, pred1, pred2)
    VALUES (?, ?, ?, ?)
    """,
    (message.from_user.id, match_id, p1, p2))

    db.commit()

    await message.answer("✅ پیش‌بینی ثبت شد.")


@dp.message(Command("ranking"))
async def ranking(message: types.Message):

    rows = cur.execute("""
    SELECT username, points
    FROM users
    ORDER BY points DESC
    LIMIT 20
    """).fetchall()

    if not rows:
        await message.answer("جدول خالی است.")
        return

    text = "🏅 رتبه‌بندی:\n\n"

    for i, row in enumerate(rows, start=1):
        username = row[0] if row[0] else "بدون نام"

        text += (
            f"{i}. {username} - {row[1]} امتیاز\n"
        )

    await message.answer(text)


@dp.message(Command("addmatch"))
async def addmatch(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, team1, team2 = message.text.split()

    except:
        await message.answer(
            "/addmatch Iran Japan"
        )
        return

    cur.execute(
        "INSERT INTO matches(team1, team2) VALUES (?, ?)",
        (team1, team2)
    )

    db.commit()

    await message.answer("✅ مسابقه اضافه شد.")


@dp.message(Command("result"))
async def result(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, match_id, score = message.text.split()

        s1, s2 = map(int, score.split("-"))
        match_id = int(match_id)

    except:
        await message.answer(
            "/result 1 2-1"
        )
        return

    cur.execute("""
    UPDATE matches
    SET score1=?, score2=?, finished=1
    WHERE id=?
    """,
    (s1, s2, match_id))

    predictions = cur.execute("""
    SELECT user_id, pred1, pred2
    FROM predictions
    WHERE match_id=?
    """,
    (match_id,)).fetchall()

    for user_id, p1, p2 in predictions:

        points = 0

        if p1 == s1 and p2 == s2:
            points = 3

        elif (
            (p1 > p2 and s1 > s2)
            or
            (p1 < p2 and s1 < s2)
            or
            (p1 == p2 and s1 == s2)
        ):
            points = 1

        cur.execute(
            "UPDATE users SET points = points + ? WHERE user_id=?",
            (points, user_id)
        )

    db.commit()

    await message.answer(
        "✅ نتیجه ثبت شد و امتیازات محاسبه شد."
    )


async def main():
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
