from project import bot, token, scheduler

if __name__ == "__main__":
    scheduler.start()
    bot.run(token)
