from time import sleep,time
import os
import sys
import io
import string

import pygame
from pyfiglet import Figlet

from cameras import *
from start import *
from item import *
from container import *
from map import *
from player import *
from npc import npc,npcs

lift_power = False
debugMode = False
playing = True

def type_print(val, time):
    global typing_sound
    typing_sound.stop()

    if debugMode:
        time = 0  # Just allows for quicker navigation around the game
    else:
        typing_sound.play(loops=-1)
    for x in val:
        
        print(x, end='')
        sys.stdout.flush()
        sleep(time)


def parse_input(user_input):
    blacklist = ["please", "towards", "a", "i", "if", "into", "me", "to"]
    user_input = user_input.strip()
    user_input = "".join(ch for ch in user_input if ch not in string.punctuation).lower()  # Removes punctuation
    user_input = [word for word in user_input.split() if word not in blacklist]  # Removes blacklist words
    return user_input


def print_room():
    current_room = rooms[player.location]
    type_print(f"\n{current_room.name.upper()}, FLOOR {current_room.floor}\n", 0.1)

    if not current_room.explored:  # trying to prevent long descriptions getting annoying
        type_print(f"{current_room.description}\n", 0.03)


def print_menu():
    current_room = rooms[player.location]
    type_print("You can:\n", 0.1)
    sleep(0.3)
    for door in current_room.doors:
        if "lift" in current_room.id:
            print(f" - GO to FLOOR {rooms[door].floor}.")
        else:
            print(f" - GO to {rooms[door].name.upper()}.")

    for i in current_room.items:
        item = items[i]
        if item.id[:9] == "item_note":
            print(f" - READ {item.name.upper()}.    (Adds to inventory also)")
        else:
            print(f" - TAKE {item.name.upper()}.")

    for c in current_room.containers:
        con = containers[c]
        print(f" - OPEN {con.name.upper()}.")

    if current_room.id == "room_power_3":  # power room
        print(" - USE POWER SWITCH")

    if current_room.id == "room_security":
        print(" - USE CCTV")

    if current_room.id == "room_maintenance_3" and "item_fork" in player.inventory:
        global tried_power
        if tried_power and rooms["room_power_3"].locked:
            print(" - USE FORK")
    
    if current_room.npc:
        npc=npcs[current_room.npc]
        print(f" - SPEAK to {npc.name}")
        if npc.will_take:
            for item in npc.will_take:
                if item in player.inventory:
                    print(f" - GIVE {items[item].name} to {npc.name}")
    
    print(" - OPEN INVENTORY")


def execute_view():
    # view all notes

    x = 0
    for item in player.inventory:
        if "note" in item:
            x = x + 1
            type_print(f"Note {str(x)}:", 0.2)
            print('')
            filename = f"text/{items[item].description}"
            with io.open(filename, "r", encoding="utf8") as f:
                type_print("".join(f.readlines()), 0.001)
            print("")
            print("")
    print("---------------------END OF NOTES---------------------")


def execute_help():
    print("--------- HELP MENU ---------")
    print("The following commands can be used throughout the game, but not necessarily right now:")
    print("- GO <target> --> Goes to the target room (Can do 'GO 1' to go room 1)")
    print("- TAKE <item> --> Adds item to inventory")
    print("- USE <item> --> Uses item often entering a menu/minigame")
    print("- OPEN <container> --> Opens and searches the container, and drops items on floor to be picked up")
    print("- READ <note> --> Displays a the note")
    print("- SPEAK (to) <name> --> Initiates a conversation between you and a character")
    print("- GIVE <item> --> Gives item from your inventory to character")

def command(user_input):
    cmd = user_input.pop(0)
    args = " ".join(user_input)
    if cmd == "go":
        execute_go(args)
    elif cmd == "open":
        if "inventory" in args:
            open_inventory()
        else:
            execute_open(args)
    elif cmd == "take":
        execute_take(args)
    elif cmd == "read":
        if not args:  # limited to 1 note per room as of now
            args = "note"
        execute_read(args)
    elif cmd == "use":
        execute_use(args)
    elif cmd == "speak":
        execute_speak(args)
    elif cmd == "give":
        execute_give(args)
    elif cmd == "help":
        execute_help()

    else:
        print("You cant do that.")

def execute_give(item):
    current_room = rooms[player.location]
    npc=npcs[current_room.npc]
    msg=f"{npc.name} does not want {item}."
    for i in npc.will_take:
        if items[i].name.lower() == item:
            if i in player.inventory:
                npc.take_item(i)
                player.inventory.remove(i)
                msg=f"{npc.name} took {item}."
                break
            else:
                msg=f"You do not have {item}."
                break
    print(msg)
        
                

def execute_speak(args):
    current_room = rooms[player.location]
    if args in npcs:
        npc=npcs[args]
        npc.speak()
        if npc.items:
            for item in npc.items:
                current_room.items.append(item)

def open_inventory():
    print("\nYou have:")

    contains_notes = False
    if len(player.inventory)<1:
        print("An empty inventory")
    else:
        for i in player.inventory:
            item = items[i]
            print(f" -  {item.name}.")
            if "note" in item.name.lower():
                contains_notes = True

    print("")
    if contains_notes:
        view = parse_input(input("Would you like to view all notes (Y/N)?:\n>> ").lower())
        if 'y' in view:
            execute_view()


def execute_read(note):
    current_room = rooms[player.location]
    for i in current_room.items:
        if note.lower() == items[i].name.lower():
            type_print("The note reads: \n", 0.1)
            filename = f"text/{items[i].description}"
            with io.open(filename, "r", encoding="utf8") as f:
                print("".join(f.readlines()))
            print("")
            player.inventory.append(items[i].id)
            current_room.items.remove(items[i].id)
            break
    else:
        print(f"There is no {note} in here...")


def execute_use(tool):
    current_room = rooms[player.location]
    if current_room.id == "room_security":
        play_camera()
        clear()
        type_print("Is.. Is that me?\n", 0.2)
        type_print("I don't remember a thing from last night.\n", 0.2)
        type_print("What was i doing?\n", 0.2)
        print('')
        return

    if "power switch" in tool or "fork" in tool:
        if tool == "power switch" and "power" in current_room.name.lower():
            type_print("Lift powered on!\n", 0.2)

            global lift_power
            lift_power = True
            # use power switch

        if "fork" in tool and current_room.id == "room_maintenance_3":
            if "item_fork" in player.inventory:
                if lock_pick():
                    rooms["room_power_3"].locked = False
                    rooms["room_power_3"].description = "Maintenance room"
                    type_print("Door unlocked!\n", 0.2)
                    enter = parse_input(input("Enter room now? (Y/N):\n>> ").lower())
                    if "y" in enter:
                        player.move("room_power_3")

            else:
                print("You do not have a fork")

    else:
        type_print("You cannot use that.", 0.2)

def try_security():
    print("The door to the security room is locked. There is a security panel used to unlock the door.")
    print("Instructions: \n Hack the security panel by typing the letters which come up on the screen fast enough.")
    input("Press ENTER when ready")
    print("-----------------------")
    if hack_security():
        print("SUCCESS!")
        rooms["room_security"].locked = False
        enter = parse_input(input("Enter room now? (Y/N):\n>> ").lower())
        if "y" in enter:
            player.move("room_security")
    else:
        print("Failed")
    
def hack_security():
    for i in range(3,0,-1):
        print("Starting in: " + str(i))
        sleep(1)
    print("GO!\n")
    while True:
        letter=random.choice(string.ascii_lowercase)
        time1=time()
        user_input=input(f"{letter}\n>> ").lower()
        time2=time()
        print('')
        if user_input != letter:
            print("Failed.")
            return False
        elif time2-time1 >= 1.5 :
            print("Too slow. Failed")
            return False
        else:
            if random.randint(0,10) == 7:   # 10% chance
                print("Door opened.")
                return True

def try_therapy():
    if "item_finished_note" in player.inventory:
        print("Welcome! You're late John! How have you been?")
        rooms["therapist_office"].locked = False
        sleep(1)
        global playing
        playing = False
        filename = f"text/ending3.txt"
        with io.open(filename, "r", encoding="utf8") as f:
            type_print("".join(f.readlines()), 0.001)
        print("")

        roll_credits()
    else:
        type_print("\nSorry, Dr. Paul is busy. Do you have an appointment?\n", 0.1)


def try_bar():
    if "item_bar_card" in player.inventory:
        print("Welcome, cardholder.")
        rooms["bar"].locked = False
        sleep(1)
        global playing
        playing = False
        filename = f"text/ending2.txt"
        with io.open(filename, "r", encoding="utf8") as f:
            type_print("".join(f.readlines()), 0.001)
        print("")

        roll_credits()
    else:
        type_print("\nSorry mate, members only.\n", 0.1)


def try_lift():
    if ("item_keycard" in player.inventory or "item_master_keycard" in player.inventory) and not rooms["lift_3"].explored:
        type_print("Unlocked lift!\n", 0.2)
        for rm in rooms:
            if "lift" in rm:
                rooms[rm].explored = True
                rooms[rm].locked = False

    # power
    if not lift_power and "item_keycard" in player.inventory:
        type_print("No power! Cannot go anywhere...", 0.1)

    for rm in rooms:
        if "lift" in rm:
            if not lift_power:
                rooms[rm].doors.clear()

                # add current hallway
                flr = rooms[rm].floor
                hallway_string = "hallway_" + str(flr)
                rooms[rm].doors.append(hallway_string)
            else:
                rooms[rm].doors = ["hallway_3", "hallway_2", "hallway_1"]
                if "item_master_keycard" in player.inventory:
                    rooms[rm].doors = ["hallway_4","hallway_3", "hallway_2", "hallway_1","hallway_0"]

def roll_credits():
    type_print("\n------- C R E D I T S -------\n", 0.1)
    type_print("Programmers:\n", 0.1)
    type_print("- David Priehoda\n", 0.1)
    type_print("- Fin Cottle\n", 0.1)
    type_print("- Oscar Russell\n", 0.1)
    print('')
    type_print("Story:\n", 0.1)
    type_print("- Zbyszek Kanabrodzki\n", 0.1)
    print('')
    type_print("Testing:\n", 0.1)
    type_print("- Tayeeb Islam\n", 0.1)
    print('')
    type_print("Fuck all:\n",0.1)
    type_print("- Amarvir Kandhola\n",0.1)
    type_print("- George Pop\n",0.1)
    type_print("- James Stamp\n",0.1)
    type_print("\nThank you for playing Blok.\n", 0.1)


def check_full_outfit():
    required_items = ["item_shoes", "item_coat", "item_trousers", "item_shirt"]
    missing_items = []
    for i in required_items:
        if i not in player.inventory:
            missing_items.append(i)
    return missing_items


def execute_go(door):
    current_room = rooms[player.location]

    # ending 1
    if door == "exit" and current_room.id == "hallway_0":
        missing_items = check_full_outfit()
        if len(missing_items) == 0:  # if no missing items
            type_print("You made it out!\n", 0.2)

            filename = f"text/ending1.txt"
            with io.open(filename, "r", encoding="utf8") as f:
                type_print("".join(f.readlines()), 0.001)
            print("")

            roll_credits()
            global playing
            playing = False
            return
        else:
            type_print("\nBefore you can leave you must collect your:\n", 0.1)
            for i in missing_items:
                print(f" - {items[i].name}")

    for i in current_room.doors:
        # alias to allow for "go  1"
        if door == rooms[i].name.lower() or door == rooms[i].alias.lower():
            if rooms[i].id.lower() == "lift_3" or rooms[i].id.lower() == "lift_1":
                try_lift()

            if rooms[i].locked:
                if rooms[i].id == "bar":
                    try_bar()
                elif rooms[i].id == "therapist_office":
                    try_therapy()
                elif rooms[i].id == "room_security": #If security room
                    try_security()
                else:
                    type_print("Door locked!\n", 0.1)
                    type_print(rooms[i].description + "\n", 0.1)
                    if "power" in rooms[i].id.lower():
                        global tried_power
                        tried_power = True
            else:
                if rooms[i].interactable:
                    player.move(i)
                else:
                    type_print(rooms[i].description, 0.05)
                    print('')
                    return

                # if currently in lift
                if "lift" in current_room.id and current_room.floor != rooms[i].floor:
                    global lift_sound
                    pygame.mixer.Channel(3).set_volume(0.6)
                    pygame.mixer.Channel(3).play(lift_sound)
                    print("Elevator moving...")
                    if not debugMode:
                        sleep(4)
                    pygame.mixer.Channel(3).fadeout(1000)
                # if going into lift
                elif "lift" in i:
                    if lift_power:
                        global lift_door_sound
                        lift_door_sound.play()
                else:
                    global door_sound
                    door_sound.play()
                break
            break
    else:
        print("That door doesn't exist")


def open_container(container):
    current_room = rooms[player.location]
    type_print(f"You open the {container.name}, and find:\n", 0.1)
    for i in container.contents:
        type_print(" - " + items[i].name + "\n", 0.1)
        current_room.items.append(i)


def execute_open(con):  # opening a container adds the items to the room, so they come up in the take menu
    current_room = rooms[player.location]
    for c in current_room.containers:  # checking all containers
        if con.lower() == containers[c].name.lower():  # making sure correct container
            if not containers[c].locked:  # checking if container locked
                open_container(containers[c])
                current_room.containers.remove(c)
                break
            else:
                type_print(f"{containers[c].name} is locked!", 0.2)
                attempt = input("\nEnter the code:     (or press ENTER if unknown)\n>> ")
                if attempt.lower() == containers[c].access_code.lower():
                    type_print("Access Granted!\n\n", 0.1)
                    open_container(containers[c])
                    current_room.containers.remove(c)
                else:
                    type_print("Access denied.\n", 0.1)
                break

    else:
        print(f"You can't open {con}...")


def execute_take(item):  # maybe add "take book and shoes" to add both??
    current_room = rooms[player.location]
    global pickup_sound
    if item == "all":
        if len(current_room.items) == 0:
            print("There is nothing here")
            return
        pickup_sound.play()
        for i in current_room.items:
            type_print(f"{items[i].name} added to inventory.\n", 0.1)
            player.inventory.append(items[i].id)
        current_room.items.clear()
        check_scraps()
    else:  
        for i in current_room.items:
            if item.lower() == items[i].name.lower():
                pickup_sound.play()
                type_print(items[i].description, 0.1)
                print('')
                type_print(f"{items[i].name} added to inventory.\n", 0.1)
                player.inventory.append(items[i].id)
                current_room.items.remove(items[i].id)
                check_scraps()
                break
        else:
            print(f"There is no {item} in here...")

def check_scraps():
    scraps=["item_scrap1","item_scrap2","item_scrap3","item_scrap4"]
    if set(scraps).issubset(player.inventory):   #If the player has all the scraps of paper
        print("You join all the scraps together. The new note reaveals a message")
        for scrap in scraps:
            player.inventory.remove(scrap)
        player.inventory.append("item_finished_note")

def lock_pick():
    if debugMode:
        return True
    type_print("\nYou can use the fork to pick the lock.", 0.1)
    type_print("\n\nInstructions:\nRead and type given instructions before time runs out", 0.1)
    instructions=["Twist left","Twist right","Pull back","Push"]
    input("\nPress enter when ready.")
    while True:
        instruction = random.choice(instructions)
        print(instruction)
        time1=time()
        user_input=input(">> ")
        time2=time()
        time_taken=time2-time1
        if time_taken < 4:
            if user_input.lower() == instruction.lower():
                if random.randint(0,6)==1:
                    break
            else:
                print("Wrong move, lockpicking failed.\n")
                return False
        else:
            print("Too slow, lockpicking failed.\n")
            return False
    print("Lock picked\n")
    return True


def menu():
    print("-----------------------------")
    print_room()
    rooms[player.location].explored = True
    print('')
    sleep(0.5)
    print_menu()

    global typing_sound
    typing_sound.stop()

    user_input = input("\n>> ")
    user_input = parse_input(user_input)
    if len(user_input)>0:
        command(user_input)


def init_sounds():
    pygame.mixer.music.load("sounds/background.wav")
    pygame.mixer.music.play(-1)

    global typing_sound
    typing_sound = pygame.mixer.Sound('sounds/typewriter.wav')
    typing_sound.set_volume(0.1)

    global door_sound
    door_sound = pygame.mixer.Sound('sounds/Door opening.wav')
    door_sound.set_volume(0.3)

    global lift_sound
    lift_sound = pygame.mixer.Sound('sounds/Lift 1.wav')
    lift_sound.set_volume(0.3)

    global lift_door_sound
    lift_door_sound = pygame.mixer.Sound('sounds/lift_door_open.wav')
    lift_door_sound.set_volume(0.6)

    global pickup_sound
    pickup_sound = pygame.mixer.Sound('sounds/itempickup.wav')
    pickup_sound.set_volume(0.3)


def main():
    global player
    player = Player()
    
    mode = startScreen()
    if mode == "debug":
        global debugMode
        global lift_power
        debugMode = True
        lift_power=True
        rooms["lift_1"].locked = False
        rooms["lift_2"].locked = False
        rooms["lift_3"].locked = False
        print(f"SAFE CODE lift--- {containers['safe_room2'].access_code}")
        print(f"SAFE CODE master--- {containers['safe_room4_floor_1'].access_code}")


    init_sounds()

    global playing
    global tried_power
    playing = True
    tried_power = False

    while playing:
        menu()


if __name__ == '__main__':
    pygame.mixer.init()
    clear()
    main()
