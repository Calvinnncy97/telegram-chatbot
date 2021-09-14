from datetime import date, datetime, time, timedelta
import random
from threading import TIMEOUT_MAX

from scraper.kickstarter_scraper import kickstarter_scraper
from scraper.indiegogo_scraper import indiegogo_scraper
from scraper.product_hunt_scraper import product_hunt_scraper
from server.user import User
from server.firestore import Firestore
from server.options import sources, interests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, callbackquery, chat
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)
import logging
import os

sources_index = list(range(len(sources)))
interests_index = list(range(len(interests)))

def main ():
    PORT = int(os.environ.get('PORT', 8443))
    TOKEN = "1634506742:AAHG73RFafEhaRzg9VNOHSqY_sclGoVmAjk"
    updater = Updater(token=TOKEN, use_context=True, request_kwargs={'read_timeout': 10, 'connect_timeout': 10})
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(update_source, pattern='^update_source'))
    dispatcher.add_handler(CallbackQueryHandler(update_interest, pattern='^update_interest'))
    dispatcher.add_handler(CallbackQueryHandler(update_user, pattern='^user'))
    updater.job_queue.run_daily(
        callback=update_projects,
        time=time(hour=0, minute=0, second=0)
    )
    updater.job_queue.run_repeating(
        callback=update_feed_for_all_users, 
        interval=timedelta(hours=random.randint(0,2), minutes=random.randint(0,59)),
        first= time(hour=9),    
        last=time(hour=23, minute=59),        
    )
    updater.job_queue.run_repeating(
        callback=wake_heroku,
        interval=timedelta(minutes=25)
    )
    updater.job_queue.start()
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN,
                          webhook_url='https://glacial-coast-67656.herokuapp.com/' + TOKEN)
    updater.idle()



def start (update: Update, context: CallbackContext):
    if not Firestore.check_user(str(update.effective_user.id)):
        user = User(handle=update.effective_user.full_name)
        Firestore.create_user(str(update.effective_user.id), user.get_dict())

    state = "update_source"
    keyboard = [
        [
            InlineKeyboardButton("Kickstarter", callback_data=create_callback_string(new_state=state, new_query="0")),
            InlineKeyboardButton("Indiegogo", callback_data=create_callback_string(new_state=state, new_query="1")),
            InlineKeyboardButton("PH", callback_data=create_callback_string(new_state=state, new_query="2")),
        ],
        [
            InlineKeyboardButton("Confirm", callback_data=create_callback_string(new_state="interest"))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, 
                            text="Cool! Where do you want to discover from?\n\nPS: PH is Product Hunt", 
                            reply_markup=reply_markup)



def update_source (update: Update, context: CallbackContext):
    #chosen source is encoded with the index of the list -> sources 
    update_query = update.callback_query
    state, query, chosen_sources, chosen_interests = update_query.data.split(".")
    chosen_sources = chosen_sources.split("-")

    #TODO: check user from database and pull it from there

    if query in chosen_sources:
        chosen_sources.remove(query)
    elif query != "#":
        chosen_sources.append(query)
    chosen_sources_string = "-".join(chosen_sources)

    keyboard = [[]]
    for i, source in enumerate(sources):
        callback = create_callback_string(callback_string=update_query.data, 
                                        new_state="update_source", 
                                        new_query=str(i),
                                        new_chosen_sources=chosen_sources_string)
        if source != "PH":
            source = source.capitalize()
        if str(i) in chosen_sources:
            source = source + ' ✅'
        keyboard[0].append(InlineKeyboardButton(source, callback_data = callback))
    keyboard.append([InlineKeyboardButton("Confirm", callback_data=create_callback_string(callback_string=update_query.data, 
                                                                                            new_state="update_interest", 
                                                                                            new_chosen_sources=chosen_sources_string))])
    reply_markeup = InlineKeyboardMarkup(keyboard)

    update_query.edit_message_text(text="Cool! Where do you want to discover from?\n\nPS: PH is Product Hunt", reply_markup=reply_markeup)



def update_interest (update: Update, context: CallbackContext):
    #chosen interest is encoded with the index of the list -> interests 
    update_query = update.callback_query
    state, query, chosen_sources, chosen_interests = update_query.data.split(".")
    chosen_interests = chosen_interests.split("-")
    
     #TODO: check user from database and pull it from there

    if query in chosen_interests:
        chosen_interests.remove(query)
    elif query != "#":
        chosen_interests.append(query)
    chosen_interests_string = "-".join(chosen_interests)

    keyboard = []
    row = []
    for i, interest in enumerate(interests):
        callback = create_callback_string(callback_string=update_query.data, 
                                            new_state="update_interest", 
                                            new_query=str(i), 
                                            new_chosen_interests=chosen_interests_string)
        if str(i) in chosen_interests:
            interest = interest + '  ✅'
        row.append(InlineKeyboardButton(interest.capitalize(), callback_data = callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("Confirm", callback_data=create_callback_string(callback_string=update_query.data, 
                                                                                            new_state="user",  
                                                                                            new_chosen_interests=chosen_interests_string))])
    keyboard.append([InlineKeyboardButton("Back", callback_data=create_callback_string(callback_string=update_query.data, 
                                                                                            new_state="update_source",  
                                                                                            new_chosen_interests=chosen_interests_string))])
    reply_markeup = InlineKeyboardMarkup(keyboard)

    update_query.edit_message_text(text="Awesome choices! What kind of projects would you like to see?", reply_markup=reply_markeup)



def update_user (update:Update, context: CallbackContext):
    update_query = update.callback_query
    state, query, chosen_sources, chosen_interests = update_query.data.split(".")
    source_list = chosen_sources.split("-")
    interest_list = chosen_interests.split("-")
    if "#" in source_list:
        source_list.remove("#")
    if "#" in interest_list:
        interest_list.remove("#")

    user = User(update.effective_chat.full_name, interest_list, source_list)
    Firestore.update_user(str(update.effective_chat.id), user.get_dict())


    context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Fantastico! New projects will come your way soon!", 
    )

    # update_feed(update, context)

   



def update_projects (context: CallbackContext):
    existing_projects = [j.to_dict()['title'] for j in Firestore.get_projects()]
    projects_list = [i for x in interests for i in kickstarter_scraper(x) if i.title not in existing_projects] 
    projects_list.extend([i for x in interests for i in indiegogo_scraper(x) if i.title not in existing_projects])
    projects_list.extend([i for i in product_hunt_scraper() if i.title not in existing_projects])

    for project in projects_list:
        Firestore.add_projects(project.title, project.get_dict())
    



# def update_feed (update:Update, context: CallbackContext):
#     '''
#         TODO: 
#         1. Get a list of projects relevant to user's interest and sources
#         2. Find projects which are new to user
#         3. Shuffle the sequence
#         4. Design the message
#         5. Send them at random interval 
#     '''
#     print ("update_feed")
#     if Firestore.check_user(str(update.effective_user.id)):
#         user = Firestore.get_user(str(update.effective_chat.id))
#         projects =  [x.to_dict() for x in Firestore.getInstance().collection(u'projects').where(u"sent_users", u'not-in', [[update.effective_user.id]]).stream()]
#         projects = [i for i in projects if i['category'] != "" if str(interests.index(i['category'])) in user['interests'] and str(sources.index(i['source'])) in user['sources']]
#         print ("user verified")
#         print (len(projects))
#         context.job_queue.run_once (
#             callback=send_project,
#             when=3,
#             context=[int(update.effective_user.id),projects]
#         )
        
#         remove_job_if_exists(f"update feed {update.effective_user.id}", context)

#         context.job_queue.run_repeating(
#                                     callback=send_project, 
#                                     interval=timedelta(hours=random.randint(0,2), minutes=random.randint(0,59)),
#                                     first= time(hour=9),    
#                                     last=time(hour=23, minute=59),        
#                                     context=[int(update.effective_user.id),projects],
#                                     name=f"update feed {update.effective_user.id}"
#                                     )
#         context.job_queue.start()



def update_feed_for_all_users (context: CallbackContext):
    for user in Firestore.getInstance().collection("users").stream():
        user = Firestore.get_user(user.id)
        projects =  [x.to_dict() for x in Firestore.getInstance().collection(u'projects').where(u"sent_users", u'not-in', [[user.id]]).stream()]
        projects = [i for i in projects if i['category'] != "" if str(interests.index(i['category'])) in user['interests'] and str(sources.index(i['source'])) in user['sources']]

        remove_job_if_exists(f"update feed {user.id}", context)

        context.job_queue.run_repeating(
                                    callback=send_project, 
                                    interval=timedelta(hours=random.randint(0,2), minutes=random.randint(0,59)),
                                    first= time(hour=9),    
                                    last=time(hour=23, minute=59),        
                                    context=[user.id, projects.pop(random.randint(0,len(projects)-1))],
                                    name=f"update feed {user.id}"
                                    )
        context.job_queue.start()
 


def send_project (context: CallbackContext):
    user_id, project = context.job.context
    if project == None:
        print ("There is no project")
        return

    message = f"*{project['title']}*\n\n{project['description']}\n\nImage/Content Source: [{project['source'].capitalize()}]({project['link']})"

    photos = []
    for pic in project['pictures']:
        photos.append(InputMediaPhoto(media=pic, caption=message, parse_mode='Markdown'))
        message=None
        if len(photos)>=5:
            break

    context.bot.send_media_group(
        chat_id=user_id,
        media = photos,
        timeout=30
    )

    Firestore.update_sent_projects(project['title'], str(user_id))



def create_callback_string (callback_string = "", new_state = "", new_query = "", new_chosen_sources = "", new_chosen_interests = ""):
    n = len(callback_string.split('.'))
    if n < 4:
        callback_string = callback_string + ".#"*(4-n)
    state, query, chosen_sources, chosen_interests = callback_string.split(".")
    
    if new_query != "":
        query = new_query
    elif  state != new_state:
        query = "#"

    if new_state != "":
        state = new_state

    if new_chosen_sources != "":
        chosen_sources = new_chosen_sources
    
    if new_chosen_interests != "":
        chosen_interests = new_chosen_interests

    return ".".join([state, query, chosen_sources, chosen_interests])



def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True



def wake_heroku (context:CallbackContext):
    print ("I am alive")



if __name__ == "__main__":
    main()