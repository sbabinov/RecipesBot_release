import asyncio

from aiogram import Dispatcher


async def on_startup(dp: Dispatcher):
    from utils.notify_admins import on_startup_notify

    await on_startup_notify(dp)
    print("Бот запущен")

    from utils.set_bot_commands import set_default_commands

    await set_default_commands(dp)

    from handlers.menu.repeat_events import scheduler
    asyncio.create_task(scheduler())
    # from handlers.menu.quizzes import delete_user_ids
    # loop = dp.loop
    # loop.run_until_complete(delete_user_ids())

# запуск бота
if __name__ == "__main__":
    from aiogram import executor, Dispatcher
    from handlers import dp

    from loader import cursor, connection

    cursor.execute("""CREATE TABLE IF NOT EXISTS recipes (
        			id INT,
        			title TEXT,
        			type TEXT,
        			description TEXT,
        			ingredients TEXT,
        			tags TEXT,
        			author_id INT,
        			date TEXT
        			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS user_ids (
        			id BIGINT,
        			ids TEXT,
        			create_time INT, 
        			type TEXT
        			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS recipes_on_moder (
            			id INT,
            			title TEXT,
            			description TEXT,
            			ingredients TEXT,
            			author_id INT,
            			date TEXT
            			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS feedback (
            			rec_id INT,
            			likes TEXT,
            			favorites TEXT
            			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS profiles (
                		id INT,
                		name TEXT,
                		gender TEXT,
                		emoji TEXT,
                		favorites TEXT,
                		recipes TEXT,
                		subscriptions TEXT,
                		subscribers TEXT,
                		likes TEXT,
                		create_date TEXT,
                		lvl INT, 
                		VIP INT,
                		get_VIP_date TEXT,
                		filters TEXT,
                		achievements TEXT,
                		articles TEXT
                		)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS articles (
            			id INT,
            			title TEXT,
            			description TEXT,
            			author_id INT,
            			date TEXT, 
            			likes TEXT,
            			views TEXT
            			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS articles_on_moder (
                			id INT,
                			title TEXT,
                			description TEXT,
                			author_id INT
                			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS comments (
                			id INT,
                			article_id INT,
                			author_id INT,
                			text TEXT
                			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS timers (
                   			user_id INT,
                   			timer_time INT,
                   			timer_note TEXT
                   			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS timers_work (
                       			timer_id INT,
                       			if_works INT,
                       			user_id INT
                       			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS notifications (
                           			user_id INT,
                           			if_turn_on INT
                           			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS experience (
                               			user_id INT,
                               			for_likes TEXT,
                               			for_favorites TEXT,
                               			for_comments TEXT,
                               			for_sub TEXT
                               			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS help (
                               			id INT,
                               			user_id INT,
                               			text TEXT,
                               			type TEXT
                               			)""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS statistics (
                                id INT,
                                users INT,
                                vip_users INT,
                                recipes INT,
                                articles INT,
                                timers INT,
                                timers_work INT,
                                comments INT,
                                questions INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS questions (
                                id INT,
                                text TEXT,
                                variants TEXT,
                                right_variant TEXT,
                                if_for_quiz INT,
                                users TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS questions_time (
                                user_id INT,
                                questions_amount INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users_answers (
                                user_id INT,
                                right_answers INT,
                                all_answers INT,
                                quizzes INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users_scores (
                                user_id INT,
                                score INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS bills (
                                    user_id INT,
                                    bill_id TEXT,
                                    pay_url TEXT
                                    )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS promo (
                                user_id INT,
                                user_promo TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS quiz (
                                questions_ids TEXT,
                                users TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS news (
                                id INT,
                                title TEXT,
                                text TEXT,
                                date TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS handbook (
                                id INT,
                                title TEXT,
                                text TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users_themes (
                                user_id INT,
                                theme TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS exercises (
                                id INT,
                                name TEXT,
                                text TEXT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS health_programs (
                                id INT,
                                title TEXT,
                                difficulty TEXT,
                                sex TEXT,
                                ration TEXT,
                                exercises TEXT,
                                image_id INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users_health_programs (
                                user_id INT,
                                programs_ids INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS health_statistic (
                                user_id INT,
                                finished_programs INT,
                                exercises_amount INT,
                                days TEXT,
                                days_in_a_row INT
                                )""")

    connection.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS search_criteria (
                                user_id INT,
                                title TEXT,
                                ingredients TEXT,
                                tags TEXT,
                                categories TEXT
                                )""")

    connection.commit()

    executor.start_polling(dp, on_startup=on_startup)

