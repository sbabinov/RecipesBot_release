from loader import cursor, connection


def update_experience(user_id: int, exp_amount: int):
    user_exp = cursor.execute("SELECT lvl FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]

    new_exp = user_exp + exp_amount

    cursor.execute("UPDATE profiles SET lvl = ? WHERE id = ?", (new_exp, user_id))
    connection.commit()


def give_experience(user_id: int, exp_amount: int, rec_id: int = None, for_like: bool = False, for_favor: bool = False,
                    for_comment: bool = False, for_sub: int = None):

    if_exists = cursor.execute("SELECT for_likes FROM experience WHERE user_id = ?", (user_id,)).fetchone()
    if not if_exists:
        cursor.execute("INSERT INTO experience VALUES (?, ?, ?, ?, ?)", (user_id, '', '', '', ''))
        connection.commit()

    if rec_id or rec_id == 0 or for_sub:
        if for_like:
            exp_for_likes = \
                cursor.execute("SELECT for_likes FROM experience "
                               "WHERE user_id = ?", (user_id,)).fetchone()[0].split()
            if str(rec_id) not in exp_for_likes:
                exp_for_likes.append(str(rec_id))
                exp_for_likes = ' '.join(exp_for_likes)

                cursor.execute("UPDATE experience SET for_likes = ? WHERE user_id = ?", (exp_for_likes, user_id,))
                connection.commit()

                update_experience(user_id, exp_amount)

        elif for_favor:
            exp_for_favor = \
                cursor.execute("SELECT for_favorites FROM experience "
                               "WHERE user_id = ?", (user_id,)).fetchone()[0].split()
            if str(rec_id) not in exp_for_favor:
                exp_for_favor.append(str(rec_id))
                exp_for_favor = ' '.join(exp_for_favor)

                cursor.execute("UPDATE experience SET for_favorites = ? WHERE user_id = ?", (exp_for_favor, user_id))
                connection.commit()

                update_experience(user_id, exp_amount)

        elif for_comment:
            exp_for_comment = \
                cursor.execute("SELECT for_comments FROM experience "
                               "WHERE user_id = ?", (user_id,)).fetchone()[0].split()
            if str(rec_id) not in exp_for_comment:
                exp_for_comment.append(str(rec_id))
                exp_for_comment = ' '.join(exp_for_comment)

                cursor.execute("UPDATE experience SET for_comments = ? WHERE user_id = ?", (exp_for_comment, user_id))
                connection.commit()

                update_experience(user_id, exp_amount)

        elif for_sub:
            exp_for_sub = \
                cursor.execute("SELECT for_sub FROM experience "
                               "WHERE user_id = ?", (user_id,)).fetchone()[0].split()
            if str(for_sub) not in exp_for_sub:
                exp_for_sub.append(str(for_sub))
                exp_for_sub = ' '.join(exp_for_sub)

                cursor.execute("UPDATE experience SET for_sub = ? WHERE user_id = ?", (exp_for_sub, user_id))
                connection.commit()

                update_experience(user_id, exp_amount)

        else:
            update_experience(user_id, exp_amount)
    else:
        update_experience(user_id, exp_amount)

