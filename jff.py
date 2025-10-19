import xml.etree.ElementTree as ET
import shutil
import os

JFF_FILE = r"E:\jff.jff"
BACKUP_FILE = JFF_FILE + ".bak"

def backup_jff():
    try:
        shutil.copy2(JFF_FILE, BACKUP_FILE)
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")

def get_state_name_map():
    tree = ET.parse(JFF_FILE)
    automaton = tree.getroot().find("automaton")
    id_to_name = {}
    for state in automaton.findall("state"):
        sid = state.attrib.get("id", "").strip()
        name = state.attrib.get("name", "").strip()
        if sid and name:
            id_to_name[sid] = name
    return id_to_name

def get_current_pin():
    tree = ET.parse(JFF_FILE)
    automaton = tree.getroot().find("automaton")
    pin_digits = []
    expected_pairs = [("1", "2"), ("2", "3"), ("3", "4"), ("4", "5"), ("5", "6"), ("6", "7")]

    for (frm, to) in expected_pairs:
        digit = None
        for trans in automaton.findall("transition"):
            from_state = (trans.find("from").text or "").strip()
            to_state = (trans.find("to").text or "").strip()
            read = (trans.find("read").text or "").strip() if trans.find("read") is not None else ""
            if from_state == frm and to_state == to and read.isdigit():
                digit = read
                break
        if digit:
            pin_digits.append(digit)
    return "".join(pin_digits)

def update_jff_pin(new_pin):
    new_pin = new_pin.strip()
    if len(new_pin) != 6 or not new_pin.isdigit():
        print("❌ Invalid PIN format. Must be exactly 6 digits.")
        return False

    backup_jff()
    tree = ET.parse(JFF_FILE)
    root = tree.getroot()
    automaton = root.find("automaton")

    for trans in list(automaton.findall("transition")):
        frm = trans.find("from")
        read = trans.find("read")
        if frm is None or read is None:
            continue
        from_state = (frm.text or "").strip()
        read_val = (read.text or "").strip()
        if from_state.isdigit() and 1 <= int(from_state) <= 6 and read_val.isdigit():
            automaton.remove(trans)

    states = ["1", "2", "3", "4", "5", "6", "7"]
    for i in range(6):
        t = ET.SubElement(automaton, "transition")
        ET.SubElement(t, "from").text = states[i]
        ET.SubElement(t, "to").text = states[i + 1]
        ET.SubElement(t, "read").text = new_pin[i]
        ET.SubElement(t, "pop").text = ""
        ET.SubElement(t, "push").text = ""

    tree.write(JFF_FILE, encoding="UTF-8", xml_declaration=True)
    print("🔐 PIN successfully updated.")
    return True

def verify_pin_jff(pin, show_trace=True):
    tree = ET.parse(JFF_FILE)
    automaton = tree.getroot().find("automaton")
    id_to_name = get_state_name_map()
    current_state = "1"
    state_trace = []

    for digit in pin:
        found_transition = False
        for trans in automaton.findall("transition"):
            from_state = (trans.find("from").text or "").strip()
            to_state = (trans.find("to").text or "").strip()
            read_val = (trans.find("read").text or "").strip()
            if from_state == current_state and read_val == digit:
                step = f"{id_to_name.get(from_state)} --[{digit}]--> {id_to_name.get(to_state)}"
                state_trace.append(step)
                current_state = to_state
                found_transition = True
                break
        if not found_transition:
            if show_trace:
                print("\n🧭 Traversed path before failure:")
                for s in state_trace:
                    print("   ", s)
                print(f"❌ Invalid transition at {id_to_name.get(current_state)} for input '{digit}'")
            return False

    for trans in automaton.findall("transition"):
        if (trans.find("from").text or "").strip() == current_state and \
           (trans.find("to").text or "").strip() == "8":
            state_trace.append(f"{id_to_name.get('7')} --[ε]--> {id_to_name.get('8')}")
            current_state = "8"

    if show_trace:
        print("\n🧭 Full Traversal Path:")
        for s in state_trace:
            print("   ", s)

    return current_state == "8"

def door_lock():
    attempts = 0
    max_attempts = 3

    while True:
        stored_pin = get_current_pin()
        print("\n--- 🔒 Smart Door Lock System ---")
        print("1. Enter PIN")
        print("2. Reset PIN")
        print("3. Exit")
        choice = input("Choose option: ").strip()

        if choice == "1":
            if attempts >= max_attempts:
                print("🚨 Too many failed attempts. System locked!")
                continue
            user_pin = input("Enter 6-digit PIN: ").strip()
            print("\n🔍 Processing through PDA automaton...")
            if verify_pin_jff(user_pin):
                print("✅ Correct PIN - Door Unlocked!")
                attempts = 0
            else:
                attempts += 1
                print(f"❌ Wrong PIN ({attempts}/{max_attempts})")
                if attempts >= max_attempts:
                    print("🚨 Security Alert: Access temporarily locked!")

        elif choice == "2":
            print("\n🔑 PIN Reset Mode")
            old_pin = input("Enter current 6-digit PIN: ").strip()
            print("\n🔍 Verifying current PIN through PDA automaton...")
            if verify_pin_jff(old_pin):
                print("✅ Current PIN verified successfully.")
                new_pin = input("Enter new 6-digit PIN: ").strip()
                if update_jff_pin(new_pin):
                    print("🔑 PIN successfully reset!")
                    attempts = 0
                else:
                    print("❌ Failed to update PIN.")
            else:
                print("❌ Wrong current PIN! Reset aborted.")

        elif choice == "3":
            print("👋 Exiting Smart Door Lock...")
            break

        else:
            print("❌ Invalid option. Choose 1, 2, or 3.")

if __name__ == "__main__":
    if not os.path.exists(JFF_FILE):
        print(f"Error: JFF file not found at {JFF_FILE}")
    else:
        door_lock()
