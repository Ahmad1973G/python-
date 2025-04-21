import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os

class CharacterSelectionApp:
    def __init__(self, master):
        self.master = master
        master.title("Character Selection")
        master.geometry("900x700")
        master.configure(bg='#121212')

        # Get the directory of the script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Character data with enhanced details
        self.characters = [
            {
                "name": "Warrior",
                "description": "A fierce melee fighter with unmatched strength",
                "image_path": os.path.join(self.script_dir, "images/warrior.png"),
                "stats": {
                    "Health": 85,
                    "Strength": 90,
                    "Defense": 80
                },
                "color": "#8B0000"
            },
            {
                "name": "Mage",
                "description": "A powerful arcane strategist with mystical abilities",
                "image_path": os.path.join(self.script_dir, "images/mage.png"),
                "stats": {
                    "Health": 60,
                    "Strength": 70,
                    "Defense": 50
                },
                "color": "#4A4A4A"
            },
            {
                "name": "Archer",
                "description": "A precise long-range combatant with exceptional agility",
                "image_path": os.path.join(self.script_dir, "images/archer.png"),
                "stats": {
                    "Health": 70,
                    "Strength": 65,
                    "Defense": 60
                },
                "color": "#2C3E50"
            }
        ]

        self.current_character_index = 0
        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.master, bg='#121212')
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)

        # Title
        title_label = tk.Label(
            main_frame, 
            text="Choose Your Character", 
            font=("Segoe UI", 36, "bold"), 
            bg='#121212', 
            fg='white'
        )
        title_label.pack(pady=20)

        # Navigation and Character Display Frame
        nav_frame = tk.Frame(main_frame, bg='#121212')
        nav_frame.pack(expand=True, fill=tk.BOTH)

        # Left Arrow
        left_arrow = tk.Button(
            nav_frame, 
            text="◀", 
            command=self.previous_character,
            font=("Segoe UI", 24),
            bg='#1E1E1E', 
            fg='white',
            borderwidth=0,
            activebackground='#333333'
        )
        left_arrow.pack(side=tk.LEFT, padx=20, expand=True)

        # Character Display Frame
        character_frame = tk.Frame(nav_frame, bg='#121212')
        character_frame.pack(side=tk.LEFT, expand=True)

        # Character Image Placeholder
        self.character_image_label = tk.Label(
            character_frame, 
            bg='#1E1E1E', 
            width=300, 
            height=400
        )
        self.character_image_label.pack(pady=20)

        # Character Name
        self.character_name_label = tk.Label(
            character_frame, 
            text="", 
            font=("Segoe UI", 28, "bold"), 
            bg='#121212', 
            fg='white'
        )
        self.character_name_label.pack(pady=10)

        # Character Description
        self.character_desc_label = tk.Label(
            character_frame, 
            text="", 
            font=("Segoe UI", 12), 
            bg='#121212', 
            fg='#BBBBBB',
            wraplength=400,
            justify=tk.CENTER
        )
        self.character_desc_label.pack(pady=10)

        # Stat Percentage Labels Frame
        stat_percentage_frame = tk.Frame(character_frame, bg='#121212')
        stat_percentage_frame.pack(pady=10)

        # Percentage Labels
        self.stat_percentage_labels = {}
        for stat in ["Health", "Strength", "Defense"]:
            # Container for stat label and percentage
            stat_container = tk.Frame(stat_percentage_frame, bg='#121212')
            stat_container.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)

            # Stat Label
            stat_label = tk.Label(
                stat_container, 
                text=stat, 
                font=("Segoe UI", 12), 
                bg='#121212', 
                fg='white',
                width=10,
                anchor='w'
            )
            stat_label.pack(side=tk.LEFT)

            # Percentage Label
            percentage_label = tk.Label(
                stat_container, 
                text="0%", 
                font=("Segoe UI", 12), 
                bg='#121212', 
                fg='white',
                width=5
            )
            percentage_label.pack(side=tk.RIGHT)
            self.stat_percentage_labels[stat] = percentage_label

        # Right Arrow
        right_arrow = tk.Button(
            nav_frame, 
            text="▶", 
            command=self.next_character,
            font=("Segoe UI", 24),
            bg='#1E1E1E', 
            fg='white',
            borderwidth=0,
            activebackground='#333333'
        )
        right_arrow.pack(side=tk.RIGHT, padx=20, expand=True)

        # Play Button
        self.play_button = tk.Button(
            main_frame, 
            text="START ADVENTURE", 
            command=self.start_game,
            font=("Segoe UI", 18, "bold"),
            bg='#8B0000', 
            fg='white',
            borderwidth=0,
            activebackground='#5C0000'
        )
        self.play_button.pack(pady=20)

        # Bind arrow keys
        self.master.bind('<Left>', lambda e: self.previous_character())
        self.master.bind('<Right>', lambda e: self.next_character())

        # Initial character load
        self.load_character()

    def load_character(self):
        character = self.characters[self.current_character_index]
        
        # Update image
        try:
            original_image = Image.open(character['image_path'])
            resized_image = original_image.resize((300, 400), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized_image)
            self.character_image_label.config(image=photo)
            self.character_image_label.image = photo
        except FileNotFoundError:
            print(f"Image not found: {character['image_path']}")
            # Create a placeholder color block if image is missing
            placeholder = Image.new('RGB', (300, 400), color=character['color'])
            photo = ImageTk.PhotoImage(placeholder)
            self.character_image_label.config(image=photo)
            self.character_image_label.image = photo

        # Update name and description
        self.character_name_label.config(
            text=character['name'], 
            fg=character['color']
        )
        self.character_desc_label.config(text=character['description'])

        # Update percentage labels
        for stat, value in character['stats'].items():
            self.stat_percentage_labels[stat].config(text=f"{value}%")

    def previous_character(self):
        self.current_character_index = (self.current_character_index - 1) % len(self.characters)
        self.load_character()

    def next_character(self):
        self.current_character_index = (self.current_character_index + 1) % len(self.characters)
        self.load_character()

    def start_game(self):
        selected_character = self.characters[self.current_character_index]['name']
        messagebox.showinfo(
            "Adventure Begins", 
            f"Embarking on a journey with the {selected_character}!\n"
            "Prepare for an epic quest!"
        )
        # Add your game launch logic here

def main():
    root = tk.Tk()
    app = CharacterSelectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()