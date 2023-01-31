import logging
import signal
import requests
import sys
import time

from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '5919140707:AAGe67LX34tw609uREXgL-6bY9LAGhn4vM8'
ChatID = '1029681168'
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


signal.signal(signal.SIGINT, signal_handler)


def wait_time(g_time):
    interrupted = False
    for remaining in range(g_time, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:2d} seconds remaining.".format(remaining))
        sys.stdout.flush()
        time.sleep(1)
        if interrupted:
            print("Gotta go")
            break


def batsman_data(r):
    bat = []
    for batsmen in r['supportInfo']['liveSummary']['batsmen']:
        bat.append(batsmen['player']['battingName']+'     ' +
                   str(batsmen['runs'])+'('+str(batsmen['balls'])+')')
    return bat


def bowler_data(r):
    a = []
    for bowler in r['supportInfo']['liveSummary']['bowlers']:
        a.append(bowler['player']['battingName']+'          '+str(bowler['overs'])+'-' +
                 str(bowler['maidens'])+'-'+str(bowler['conceded'])+'-'+str(bowler['wickets']))
    return a


url = requests.get(
    "https://hs-consumer-api.espncricinfo.com/v1/pages/matches/current?latest=true").json()
matches_detail = [[match['scribeId'], match['slug'], match['series']['objectId'],
                   match['series']['slug']] for match in url['matches'] if match['status'] == 'Live']
matches_detail_str = ''

for i, match_d in enumerate(matches_detail):
    matches_detail_str += f'live{i+1} --> '+str(match_d[1])+'\n'
# print(matches_detail)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi,\n I am cricket score Bot. I will update you on the live score of todays game.")

    if matches_detail:
        await message.reply(matches_detail_str)
    else:
        await message.reply('No Live coverage going on!! \n-----BYE----')


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)

    # await message.reply(message.text)

    # print(message.text.lower())
    if len(message.text) in [5, 6] and matches_detail_str.find(message.text.lower()) != -1:
        msg = message.text.strip('live')
        a = int(msg)
        print(a)
        select_match_url = f'https://www.espncricinfo.com/series/{matches_detail[a-1][3]}-{matches_detail[a-1][2]}/{matches_detail[a-1][1]}-{matches_detail[a-1][0]}/live-cricket-score'
        print(select_match_url)
        state = True
        cache = []
        while True:

            #bot.reply_to(message, message.text)
            # final_score=cricket.final_score_fun(select_match_url)
            url = f"https://hs-consumer-api.espncricinfo.com/v1/pages/match/details?seriesId={matches_detail[a-1][2]}&matchId={matches_detail[a-1][0]}&latest=true"
            print(url)
            r = requests.get(url).json()
            # if cache[0]!=cache[1]:
            if r['recentBallCommentary']:
                recent_ball = r['recentBallCommentary']['ballComments'][0]
                
                four = 'Four Runs ' if recent_ball['isFour'] else ''
                six = 'SIX Runs ' if recent_ball['isSix'] else ''
                wicket = 'OUT ' if recent_ball['isWicket'] else ''
                print(recent_ball)
                if recent_ball['oversActual'] not in cache:
                    if cache:
                        cache.pop(0)
                    cache.append(recent_ball['oversActual'])
                    if  four or six or wicket:
                        runs = '' if four or six or wicket  else str(
                            recent_ball['totalRuns'])+' Runs'
                        recent = str(
                            recent_ball['oversActual'])+' '+recent_ball['title']+', '+four+six+wicket+runs
                        print(recent)
                        await bot.send_message(ChatID, recent)  # your chat id
                    if str(recent_ball['oversActual']).find('.6') != -1:
                        batsman_info = batsman_data(r)
                        bowler_info = bowler_data(r)
                        recent_comment = r['recentBallCommentary']['ballComments'][0]
                        print(recent_comment)
                        output = str(recent_comment['over']['team']['abbreviation'])+' - '+str(recent_comment['over']['totalRuns'])+'/'+str(recent_comment['over']['totalWickets']) + ' \n ' + str(
                            recent_comment['over']['overRuns'])+' runs * '+str(recent_comment['over']['overWickets'])+' wckts'+'\n'+'batting=> '+' || '.join(batsman_info) + '\n'+'bowling=> '+' || '.join(bowler_info)
                        await bot.send_message(ChatID, output)  # your chat id
                        print(output)
                        time.sleep(30)

                    wait_time(40)
                else:
                    wait_time(30)

            else:
                await message.reply('No Live commentary available for this match')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
