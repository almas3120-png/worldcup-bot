import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789  # Telegram user id of admin

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
        "/matches - مسابقات\n"
        "/predict <match_id> <x-y>\n"
        "نمونه: /predict 1 2-1\n"
        "/ranking - جدول رتبه‌بندی"
    )


@dp.message(Command("matches"))
async def matches(message: types.Message):
    rows = cur.execute(
        "SELECT id, team1, team2, finished FROM matches"
    ).fetchall()

    if not rows:
        await message.answer("هنوز مسابقه‌ای ثبت نشده است.")
        return

    text = "📋 مسابقات:\n\n"
    for r in rows:
        status = "✅ پایان یافته" if r[3] else "⏳ باز"
        text += f"{r[0]}. {r[1]} vs {r[2]} - {status}\n"

    await message.answer(text)


@dp.message(Command("predict"))
async def predict(message: types.Message):
    register_user(message.from_user)

    try:
        _, match_id, score = message.text.split()
        p1, p2 = map(int, score.split("-"))
        match_id = int(match_id)
    except Exception:
        await message.answer("نمونه صحیح:\n/predict 1 2-1")
        return

    match = cur.execute(
        "SELECT finished FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if not match:
        await message.answer("شناسه مسابقه نامعتبر است.")
        return

    if match[0]:
        await message.answer("این مسابقه پایان یافته است.")
        return

    cur.execute("""
    INSERT OR REPLACE INTO predictions
    (user_id, match_id, pred1, pred2)
    VALUES (?, ?, ?, ?)
    """, (message.from_user.id, match_id, p1, p2))

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
        await message.answer("جدولی وجود ندارد.")
        return

    text = "🏅 رتبه‌بندی:\n\n"
    for i, row in enumerate(rows, start=1):
        text += f"{i}. @{row[0]} - {row[1]} امتیاز\n"

    await message.answer(text)


@dp.message(Command("addmatch"))
async def addmatch(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, team1, team2 = message.text.split()
    except Exception:
        await message.answer("/addmatch TeamA TeamB")
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
    except Exception:
        await message.answer("/result 1 2-1")
        return

    cur.execute("""
    UPDATE matches
    SET score1=?, score2=?, finished=1
    WHERE id=?
    """, (s1, s2, match_id))

    preds = cur.execute("""
    SELECT user_id, pred1, pred2
    FROM predictions
    WHERE match_id=?
    """, (match_id,)).fetchall()

    for user_id, p1, p2 in preds:
        pts = 0

        if p1 == s1 and p2 == s2:
            pts = 3
        elif ((p1 > p2 and s1 > s2) or
              (p1 < p2 and s1 < s2) or
              (p1 == p2 and s1 == s2)):
            pts = 1

        cur.execute(
            "UPDATE users SET points = points + ? WHERE user_id=?",
            (pts, user_id)
        )

    db.commit()
    await message.answer("✅ نتیجه ثبت و امتیازها محاسبه شد.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
