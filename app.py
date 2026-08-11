from flask import Flask, render_template, jsonify, request, session, send_from_directory
from database import (init_db, get_user, create_user, update_user, 
                     get_upgrades, set_upgrade, add_event, 
                     add_monetization_log, get_last_monetization)
from game_logic import (UPGRADES, STAGES, EVENTS, MONETIZATION,
                       calculate_upgrade_cost, get_current_stage, 
                       calculate_click_value, check_event,
                       get_available_monetization, calculate_daily_reward,
                       apply_ad_boost)
import json
import uuid
import random
import os
import time
from datetime import datetime

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'doge_empire_secret_key_2024'

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.before_request
def ensure_user():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/game-state')
def game_state():
    user_id = session['user_id']
    user = get_user(user_id)
    
    if not user:
        user = create_user(user_id)
    
    upgrades = get_upgrades(user_id)
    current_stage = get_current_stage(user['coins'])
    
    available_upgrades = {}
    for uid, uinfo in UPGRADES.items():
        if uinfo['stage_required'] <= current_stage:
            current_level = upgrades.get(uid, 0)
            available_upgrades[uid] = {
                **uinfo,
                'level': current_level,
                'cost': calculate_upgrade_cost(uid, current_level),
                'max_level': 10
            }
    
    return jsonify({
        'user': user,
        'available_upgrades': available_upgrades,
        'current_stage': STAGES[current_stage],
        'stage_id': current_stage,
        'monetization': get_available_monetization(current_stage)
    })

@app.route('/api/click', methods=['POST'])
def click():
    user_id = session['user_id']
    user = get_user(user_id)
    upgrades = get_upgrades(user_id)
    
    coins_earned, crit_type = calculate_click_value(user, upgrades)
    
    skin_bonus = user.get('skin_bonus', 1.0)
    coins_earned *= skin_bonus * user.get('multiplier', 1.0)
    
    new_coins = user['coins'] + coins_earned
    new_total = user['total_coins'] + coins_earned
    new_clicks = user['clicks'] + 1
    
    old_stage = get_current_stage(user['coins'])
    new_stage = get_current_stage(new_coins)
    
    update_user(user_id, 
                coins=new_coins, 
                total_coins=new_total, 
                clicks=new_clicks)
    
    event_result = None
    if random.random() < 0.15:
        event = check_event()
        if event:
            effect = event['effect']({'coins': new_coins})
            if 'coins' in effect:
                new_coins += effect['coins']
                update_user(user_id, coins=new_coins)
            add_event(user_id, event['id'], effect)
            event_result = {
                'name': event['name'],
                'message': effect.get('message', ''),
                'type': event['type'],
                'duration': event.get('duration', 0)
            }
    
    stage_up = new_stage > old_stage
    
    return jsonify({
        'coins': new_coins,
        'coins_earned': coins_earned,
        'total_coins': new_total,
        'clicks': new_clicks,
        'crit_type': crit_type,
        'event': event_result,
        'stage_up': stage_up,
        'new_stage': STAGES[new_stage] if stage_up else None
    })

@app.route('/api/buy-upgrade/<upgrade_id>', methods=['POST'])
def buy_upgrade(upgrade_id):
    user_id = session['user_id']
    user = get_user(user_id)
    upgrades = get_upgrades(user_id)
    
    if upgrade_id not in UPGRADES:
        return jsonify({'success': False, 'message': 'Неизвестное улучшение'})
    
    current_level = upgrades.get(upgrade_id, 0)
    cost = calculate_upgrade_cost(upgrade_id, current_level)
    
    if user['coins'] < cost:
        return jsonify({'success': False, 'message': 'Недостаточно DogeCoin!'})
    
    if current_level >= 10:
        return jsonify({'success': False, 'message': 'Максимальный уровень!'})
    
    new_level = current_level + 1
    new_coins = user['coins'] - cost
    
    upgrade = UPGRADES[upgrade_id]
    effect_updates = {}
    
    if upgrade['effect_type'] == 'click_power':
        effect_updates['click_power'] = user['click_power'] + upgrade['effect_value']
    elif upgrade['effect_type'] == 'crit_chance':
        effect_updates['crit_chance'] = min(user['crit_chance'] + upgrade['effect_value'], 1.0)
    elif upgrade['effect_type'] == 'auto_click':
        effect_updates['auto_click_power'] = user['auto_click_power'] + upgrade['effect_value']
    elif upgrade['effect_type'] == 'multiplier':
        effect_updates['multiplier'] = user['multiplier'] + upgrade['effect_value']
    
    update_user(user_id, coins=new_coins, **effect_updates)
    set_upgrade(user_id, upgrade_id, new_level)
    add_event(user_id, 'upgrade_purchased', {'upgrade': upgrade_id, 'level': new_level})
    
    return jsonify({
        'success': True,
        'coins': new_coins,
        'upgrade': {
            'id': upgrade_id,
            'level': new_level,
            'next_cost': calculate_upgrade_cost(upgrade_id, new_level)
        },
        'message': upgrade['name'] + ' улучшен до уровня ' + str(new_level) + '!'
    })

@app.route('/api/monetization/daily-reward', methods=['POST'])
def claim_daily_reward():
    user_id = session['user_id']
    user = get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    current_time = datetime.now()
    last_reward = user.get('last_daily_reward')
    
    if last_reward:
        last_reward_time = datetime.fromisoformat(last_reward)
        hours_passed = (current_time - last_reward_time).total_seconds() / 3600
        
        if hours_passed < 24:
            remaining = 24 - hours_passed
            return jsonify({
                'success': False, 
                'message': f'Следующая награда через {remaining:.1f} часов'
            })
        
        if hours_passed < 48:
            streak = (user.get('daily_streak') or 0) + 1
        else:
            streak = 1
    else:
        streak = 1
    
    reward = calculate_daily_reward(streak)
    
    update_user(
        user_id, 
        coins=user['coins'] + reward,
        daily_streak=streak,
        last_daily_reward=current_time.isoformat()
    )
    
    add_event(user_id, 'daily_reward', {
        'reward': reward,
        'streak': streak
    })
    
    return jsonify({
        'success': True,
        'reward': reward,
        'streak': streak,
        'message': f'🎉 Ежедневная награда: +{reward} DogeCoin! Серия: {streak} дней'
    })

@app.route('/api/monetization/ad-boost', methods=['POST'])
def activate_ad_boost():
    user_id = session['user_id']
    user = get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    last_boost = get_last_monetization(user_id, 'ad_boost')
    if last_boost:
        time_passed = time.time() - datetime.fromisoformat(last_boost).timestamp()
        if time_passed < MONETIZATION['ad_boost']['cooldown']:
            remaining = MONETIZATION['ad_boost']['cooldown'] - time_passed
            return jsonify({
                'success': False,
                'message': f'Буст будет доступен через {remaining:.0f} секунд'
            })
    
    boost = apply_ad_boost(user)
    add_monetization_log(user_id, 'ad_boost', 'activated', boost)
    
    return jsonify({
        'success': True,
        'multiplier': boost['multiplier'],
        'duration': MONETIZATION['ad_boost']['duration'],
        'message': boost['message']
    })

@app.route('/api/monetization/skins', methods=['GET'])
def get_skins():
    return jsonify({
        'skins': MONETIZATION['premium_skin']['skins']
    })

@app.route('/api/monetization/buy-skin/<skin_id>', methods=['POST'])
def buy_skin(skin_id):
    user_id = session['user_id']
    user = get_user(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    skin = MONETIZATION['premium_skin']['skins'].get(skin_id)
    if not skin:
        return jsonify({'success': False, 'message': 'Скин не найден'})
    
    if user['coins'] < skin['cost']:
        return jsonify({'success': False, 'message': 'Недостаточно DogeCoin!'})
    
    new_coins = user['coins'] - skin['cost']
    update_user(user_id, 
                coins=new_coins, 
                active_skin=skin_id,
                skin_bonus=skin['bonus'])
    
    add_monetization_log(user_id, 'premium_skin', 'purchased', {
        'skin_id': skin_id,
        'cost': skin['cost']
    })
    
    return jsonify({
        'success': True,
        'skin': skin,
        'coins': new_coins,
        'message': f'Скин "{skin["name"]}" активирован!'
    })

@app.route('/api/reset', methods=['POST'])
def reset_game():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)