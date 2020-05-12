import datetime
from typing import Dict

import auraxium_local as auraxium
# from auraxium import auraxium   # TODO switch to pypi version
from PlayerClass import PlayerClass


def calculate_ivi_score(character_name, service_id='example'):
    output = {}

    character_id_query = auraxium.Query('character_name', namespace='ps2', name__first_lower=character_name.lower())

    character_id_results = character_id_query.get()

    character_id = character_id_results[0]['character_id']

    # Get class accuracy
    # http://census.daybreakgames.com/get/ps2/character/5428359100720207121?c:join=characters_stat^on:character_id^to:character_id^list:1^inject_at:stats
    class_accuracy = auraxium.Query('character', character_id=character_id).set_show_fields('character_id')
    class_accuracy.join('characters_stat', on='character_id', to='character_id', is_list=True, inject_at='stats')

    class_accuracy = class_accuracy.get()

    class_stats: Dict[int, PlayerClass] = {}

    # item^on:attacker_weapon_id^to:item_id^terms:item_type_id=26'item_category_id=<100^outer:0^show:name.en
    recent_kills = auraxium.Query('characters_event', namespace='ps2', character_id=character_id, limit=500,
                                  type="KILL")
    recent_kills.join('item', on='attacker_weapon_id', to='item_id', item_type_id=26, attacker_vehicle_id=0,
                      item_category_id='<100',
                      is_outer=False, show=['name.en'])

    loadouts = {15: 'Infiltrator', 17: 'Light Assault', 18: 'Medic', 19: 'Engineer', 20: 'Heavy Assault', 21: 'MAX'}

    recent_kills_result = recent_kills.get()

    # Find time difference between first and last kill - apply monthly accuracy scores if kills happened over the last month
    # and weekly scores if kills happened over the last week
    # Switching points are: <= 1.5 days: daily, <= 1.5 weeks: weekly, <= 1.5 months: monthly, older:forever

    oldest_kill = recent_kills_result[-1]['timestamp']
    newest_kill = recent_kills_result[0]['timestamp']

    timeframe = ""

    if newest_kill - oldest_kill <= 129600:
        timeframe = "daily"

    elif newest_kill - oldest_kill <= 907200:
        timeframe = 'weekly'

    elif newest_kill - oldest_kill <= 3888000:
        timeframe = 'monthly'

    else:
        timeframe = 'forever'

    for stat in class_accuracy[0]['stats']:  # TODO pick item more intelligently, maybe class_accuracy.index('stats')
        profile_id = stat['profile_id']
        if stat['stat_name'] == 'hit_count':
            if profile_id in class_stats:
                class_stats[profile_id].hits = stat['value_' + timeframe]
                class_stats[profile_id].hits_forever = stat['value_forever']

            else:
                class_stats[profile_id] = PlayerClass(profile_id=profile_id, hits=stat['value_' + timeframe],
                                                      hits_forever=stat['value_forever'])

        if stat['stat_name'] == 'fire_count':
            if profile_id in class_stats:
                class_stats[profile_id].shots_fired = stat['value_' + timeframe]
                class_stats[profile_id].shots_fired_forever = stat['value_forever']


            else:
                class_stats[profile_id] = PlayerClass(profile_id=profile_id, shots_fired=stat['value_' + timeframe],
                                                      shots_fired_forever=stat['value_forever'])

    for kill in recent_kills_result:
        profile_id = PlayerClass.loadout_to_profile_id(kill['attacker_loadout_id'])

        # Skip any vehicle kills that sneak through
        if kill['attacker_vehicle_id'] != 0:
            continue

        if kill['is_headshot'] == 1:
            class_stats[profile_id].headshots += 1

        class_stats[profile_id].kills += 1

    total_shots_fired = 0
    total_hits = 0
    total_kills = 0
    total_headshots = 0

    output['Playername'] = character_id_results[0]['name']['first']
    output['kills_since'] = datetime.datetime.utcfromtimestamp(oldest_kill)

    # print("Player: ", character_id_results[0]['name']['first'])
    # print("Kills since: ", datetime.datetime.utcfromtimestamp(oldest_kill).strftime('%Y-%m-%d %H:%M'))

    oldest_kill_datetime = datetime.datetime.utcfromtimestamp(oldest_kill)

    accuracy_since = None

    if timeframe == 'monthly':
        # print("Accuracy data since: ", oldest_kill.strftime('%Y-%m-01'))

        # Easiest way to get beginning of month is to generate string representation of the current day
        # And changing the day to be 1
        accuracy_since = datetime.datetime.strptime(oldest_kill_datetime.strftime('%Y-%m-01'), '%Y-%m-%d')

    if timeframe == 'weekly':
        accuracy_since = oldest_kill_datetime - datetime.timedelta(days=oldest_kill_datetime.weekday())

        # print("Accuracy data since: ",
        #       (oldest_kill_datetime - datetime.timedelta(days=oldest_kill_datetime.weekday())).strftime('%Y-%m-%d'))

    if timeframe == 'daily':
        accuracy_since = oldest_kill_datetime
        # print("Accuracy data since: ", oldest_kill_datetime.strftime('%Y-%m-%d'))

    # else:
    #     print("Accuracy data since: the beginning of time")

    output['timeframe'] = timeframe

    output['accuracy_since'] = accuracy_since

    output['timeframe_stats'] = {}

    timeframe_stats = {}

    # Generate weekly/monthly stats
    for profile_id, class_data in class_stats.items():
        try:
            # Do these first, so that the stats don't get added if there were no shots in the timeframe
            accuracy = (class_data.hits / class_data.shots_fired) * 100
            hsr = (class_data.headshots / class_data.kills) * 100

            total_shots_fired += class_data.shots_fired
            total_hits += class_data.hits
            total_kills += class_data.kills
            total_headshots += class_data.headshots

            ivi = accuracy * hsr
            if ivi == 0:
                continue

            timeframe_stats[class_data.class_name] = {'ivi': accuracy * hsr, 'accuracy': accuracy, 'hsr': hsr,
                                                      'headshots': class_data.headshots, 'kills': class_data.kills}

            # print("Class: %s - IvI: %d - ACC: %f - HSR: %f - HS: %d Kill: %d" % (
            #     class_data.class_name, accuracy * hsr, accuracy, hsr, class_data.headshots, class_data.kills))
        except ZeroDivisionError:
            continue

    output['timeframe_stats'] = timeframe_stats

    output['timeframe_ivi'] = (total_hits / total_shots_fired) * (total_headshots / total_kills) * 10000

    # print("Your overall %s accuracy IvI is: %d" % (
    #     timeframe, (total_hits / total_shots_fired) * (total_headshots / total_kills) * 10000))

    # Generate forever stats
    if timeframe != 'forever':

        output['forever_stats'] = {}

        forever_stats = {}

        # print('\nStats using all-time accuracy data')

        total_shots_fired = 0
        total_hits = 0

        for profile_id, class_data in class_stats.items():
            try:
                total_shots_fired += class_data.shots_fired_forever
                total_hits += class_data.hits_forever

                accuracy = (class_data.hits_forever / class_data.shots_fired_forever) * 100
                hsr = (class_data.headshots / class_data.kills) * 100

                ivi = accuracy * hsr
                if ivi == 0:
                    continue

                forever_stats[class_data.class_name] = {'ivi': accuracy * hsr, 'accuracy': accuracy, 'hsr': hsr,
                                                        'headshots': class_data.headshots, 'kills': class_data.kills}

                # print("Class: %s - IvI: %d - ACC: %f - HSR: %f - HS: %d Kill: %d" % (
                #     class_data.class_name, accuracy * hsr, accuracy, hsr, class_data.headshots, class_data.kills))
            except ZeroDivisionError:
                continue

        output['forever_stats'] = forever_stats

        output['forever_ivi'] = (total_hits / total_shots_fired) * (total_headshots / total_kills) * 10000

        # print("Your overall forever accuracy IvI is: %d" % (
        #         (total_hits / total_shots_fired) * (total_headshots / total_kills) * 10000))

    return output
