import aioschedule
import asyncio

from .quizzes import delete_user_ids, new_quiz
from .health import update_week_statistics


async def scheduler():
    # aioschedule.every().sunday.at('00:01').do(new_quiz)
    aioschedule.every(30).minutes.do(delete_user_ids)
    aioschedule.every().monday.at('00:01').do(update_week_statistics)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
