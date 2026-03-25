import os
import sys
import subprocess
import shlex

def get_triggers(triggers_dir):
    """Scan the triggers directory for trigger scripts and return a dict mapping friendly names to filenames."""
    triggers = {}
    if not os.path.exists(triggers_dir):
        return triggers
        
    for filename in sorted(os.listdir(triggers_dir)):
        if filename.startswith("trigger_") and filename.endswith(".py"):
            friendly_name = filename.replace("trigger_", "").replace(".py", "")
            triggers[friendly_name] = filename
    return triggers

def display_menu(triggers_dict):
    """Display the available triggers as a numbered menu."""
    friendly_names = list(triggers_dict.keys())
    print("\n" + "═"*50)
    print(" 🚀 N8N Trigger Client Manager 🚀")
    print("═"*50)
    for i, name in enumerate(friendly_names):
        display_name = name.replace("_", " ").title()
        print(f"  {i + 1}. {display_name} ({name})")
    print("  0. Exit")
    print("═"*50)
    return friendly_names

def interactive_mode(triggers_dir, triggers_dict):
    if not triggers_dict:
        print(f"❌ No trigger scripts found in: {triggers_dir}")
        return
        
    friendly_names = list(triggers_dict.keys())
    while True:
        display_menu(triggers_dict)
        try:
            choice = input("\nSelect a trigger to run (or 0 to exit): ").strip()
            
            if choice == '0' or choice.lower() in ['q', 'quit', 'exit']:
                print("👋 Goodbye!")
                break
                
            idx = int(choice) - 1
            if 0 <= idx < len(friendly_names):
                selected_name = friendly_names[idx]
                selected_script = triggers_dict[selected_name]
                script_path = os.path.join(triggers_dir, selected_script)
                
                print(f"\n[Selected: {selected_name}]")
                args_input = input("Enter arguments (optional, press Enter to skip): ").strip()
                
                cmd = [sys.executable, script_path]
                if args_input:
                    # Safely split the arguments string like a typical shell
                    cmd.extend(shlex.split(args_input))
                
                print(f"\n--- Running {selected_script} ---")
                try:
                    # Pass control to the script (including interactive ones like conversation)
                    subprocess.run(cmd)
                except KeyboardInterrupt:
                    print(f"\n[Interrupted]")
                except Exception as e:
                    print(f"\n❌ Failed to run script: {e}")
                    
                print("-" * 50)
                input("Press Enter to continue...")
            else:
                print("⚠️  Invalid selection. Please choose a valid number.")
        except ValueError:
            print("⚠️  Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    triggers_dir = os.path.join(base_dir, "triggers")
    
    triggers_dict = get_triggers(triggers_dir)
    
    # CLI Mode
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ["-h", "--help", "help"]:
            print("Usage:")
            print("  python client_manager.py                 : Start interactive menu")
            print("  python client_manager.py list            : List all available triggers")
            print("  python client_manager.py <trigger> [arg] : Run a specific trigger with arguments")
            print("\nAvailable triggers:")
            for name in triggers_dict.keys():
                print(f"  - {name}")
            sys.exit(0)
            
        elif command == "list":
            if not triggers_dict:
                print(f"❌ No trigger scripts found in: {triggers_dir}")
                sys.exit(0)
            print("\nAvailable triggers:")
            for name in triggers_dict.keys():
                print(f"  - {name}")
            sys.exit(0)
            
        else:
            # Assume the command is a trigger name
            trigger_name = command
            if trigger_name not in triggers_dict:
                print(f"❌ Unknown trigger: '{trigger_name}'")
                print("Use 'list' command or '-h' to see available triggers.")
                sys.exit(1)
                
            script_path = os.path.join(triggers_dir, triggers_dict[trigger_name])
            cmd = [sys.executable, script_path] + sys.argv[2:]
            
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                sys.exit(130)  # Standard code for SIGINT
            except Exception as e:
                print(f"\n❌ Failed to run script: {e}")
                sys.exit(1)
            
            sys.exit(0)
            
    # Interactive mode (if no args provided)
    interactive_mode(triggers_dir, triggers_dict)

if __name__ == "__main__":
    main()
