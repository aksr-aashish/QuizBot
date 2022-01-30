Quiz bot - Questionnaire bot
Function: a game similar to a quiz (answer questions, get points for correct answers). It can also be used as a questionnaire, with the ability to save points.

Scheme of work
Members can register under an arbitrary name using the /start command. You can register in any groups where this bot is added (admin rights are required).
We register administrators by writing their identifier (s) (user_id) in constants.py
Admin with the help of /question command writes a question to the participants. After that, registration is temporarily terminated.
The bot sends a question to all unique groups (chat_id) where members have registered. Those. if you registered in private with a bot, the question comes there. The question is automatically pinned, it is not sent to admins.
Participants write responses by putting the hashtag #answer at the beginning of the message, only one response is accepted from each.
Messages with the answer are sent to the personal administrator, where he / she is invited to rate it at 0 or 1 or 2 points by clicking the appropriate button. Graded posts are automatically edited to indicate how many points have been awarded.
On the /round command (available only to admins), the bot writes to all the unique chat_id nicknames of the participants in the game and who earned how many points per round. These scores are added to the participant's total all-time scores (everyone can see the statistics for the /score team). Registration is open again.
On the admin command /reset, all data is deleted (participant nicknames, points, etc.).
The bot is written using the python-telegram-bot library, the database is sqlite3


### 💙 Heroku 💙
<p align="center"><a href="https://heroku.com/deploy?template=https://github.com/aksr-aashish/QuizBot"><img src="https://telegra.ph/file/4a7d5037bcdd1e74a517a.jpg" width="50"></a></p>
