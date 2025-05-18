import tkinter as tk
from tkinter import messagebox, font
from tkinter import ttk


class ModernGameLogin:
    def __init__(self, root, Socket):
        self.root = root
        self.root.title("Diablo")
        
        # Make the window full screen
        self.root.attributes('-fullscreen', True)
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set background color - dark theme with reddish tint for Diablo theme
        self.root.configure(bg="#0F0A0A")
        
        # Create custom fonts
        self.title_font = font.Font(family="Times New Roman", size=38, weight="bold")
        self.label_font = font.Font(family="Helvetica", size=14)
        self.button_font = font.Font(family="Helvetica", size=12, weight="bold")
        
        # Create style for modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.data = None
        
        # Configure styles for ttk widgets
        self.style.configure('TEntry', 
                            fieldbackground='#232323',
                            foreground='#e0e0e0',
                            insertcolor='#e0e0e0',
                            borderwidth=0,
                            relief=tk.FLAT)
        
        self.style.configure('TButton', 
                            font=self.button_font,
                            background='#2a2a2a',
                            foreground='#e0e0e0',
                            borderwidth=0,
                            focusthickness=0,
                            relief=tk.FLAT)
        
        self.style.map('TButton',
                      background=[('active', '#333333')])

        self.Socket = Socket
        self.player_data = None
        # Create widgets
        self.create_widgets(screen_width, screen_height)


    
    def create_widgets(self, screen_width, screen_height):
        # Main container frame (center aligned)
        center_frame = tk.Frame(self.root, bg="#0F0A0A", width=500, height=600)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title with fiery gradient effect for Diablo theme
        title_frame = tk.Frame(center_frame, bg="#0F0A0A", width=400)
        title_frame.pack(pady=(0, 40))
        
        title_label = tk.Label(
            title_frame, 
            text="DIABLO", 
            font=self.title_font, 
            bg="#0F0A0A", 
            fg="#C41E3A"  # Diablo red
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame, 
            text="enter the gates of hell", 
            font=("Times New Roman", 14, "italic"), 
            bg="#0F0A0A", 
            fg="#7D3C3C"  # Dark blood red
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Decorative line with gradient effect
        separator_canvas = tk.Canvas(center_frame, height=2, width=200, bg="#0F0A0A", highlightthickness=0)
        separator_canvas.pack(pady=(0, 40))
        
        # Create gradient for separator
        for i in range(200):
            # Create a gradient from dark to red to dark
            if i < 100:
                r = int(196 * (i/100))  # Gradient to C4 (196)
            else:
                r = int(196 * ((200-i)/100))  # Gradient from C4 (196) back
            separator_canvas.create_line(i, 0, i, 2, fill=f"#{r:02x}1E3A")
        
        # Login container
        login_frame = tk.Frame(center_frame, bg="#1E1A1A", width=400, height=280, bd=0)
        login_frame.pack(pady=10)
        login_frame.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Round the corners using a canvas
        def create_rounded_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
            points = [x1+radius, y1,
                      x2-radius, y1,
                      x2, y1,
                      x2, y1+radius,
                      x2, y2-radius,
                      x2, y2,
                      x2-radius, y2,
                      x1+radius, y2,
                      x1, y2,
                      x1, y2-radius,
                      x1, y1+radius,
                      x1, y1]
            return canvas.create_polygon(points, **kwargs, smooth=True)
        
        # Create background canvas for the login frame to give it rounded corners
        bg_canvas = tk.Canvas(login_frame, bg="#1E1A1A", highlightthickness=0)
        bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        bg_rect = create_rounded_rect(bg_canvas, 2, 2, 398, 278, radius=20, fill="#1E1A1A", outline="#1E1A1A")
        
        # Username
        username_frame = tk.Frame(login_frame, bg="#1E1A1A")
        username_frame.place(x=20, y=20, width=360, height=70)
        
        username_label = tk.Label(
            username_frame, 
            text="USERNAME", 
            font=("Helvetica", 10), 
            bg="#1E1A1A", 
            fg="#B45C5C"  # Reddish text
        )
        username_label.pack(anchor=tk.W)
        
        # Rounded username entry
        username_entry_frame = tk.Frame(username_frame, bg="#232323", bd=0, highlightthickness=1, highlightbackground="#C41E3A")
        username_entry_frame.pack(fill=tk.X, ipady=2, pady=(5, 0))
        username_entry_frame.pack_propagate(False)
        username_entry_frame.configure(height=40)
        
        self.username_entry = tk.Entry(
            username_entry_frame, 
            font=self.label_font, 
            bg="#232323", 
            fg="#e0e0e0", 
            insertbackground="#e0e0e0", 
            relief=tk.FLAT,
            bd=0
        )
        self.username_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Password
        password_frame = tk.Frame(login_frame, bg="#1E1A1A")
        password_frame.place(x=20, y=100, width=360, height=70)
        
        password_label = tk.Label(
            password_frame, 
            text="PASSWORD", 
            font=("Helvetica", 10), 
            bg="#1E1A1A", 
            fg="#B45C5C"  # Reddish text
        )
        password_label.pack(anchor=tk.W)
        
        # Rounded password entry
        password_entry_frame = tk.Frame(password_frame, bg="#232323", bd=0, highlightthickness=1, highlightbackground="#C41E3A")
        password_entry_frame.pack(fill=tk.X, ipady=2, pady=(5, 0))
        password_entry_frame.pack_propagate(False)
        password_entry_frame.configure(height=40)
        
        self.password_entry = tk.Entry(
            password_entry_frame, 
            font=self.label_font, 
            show="●", 
            bg="#232323", 
            fg="#e0e0e0", 
            insertbackground="#e0e0e0", 
            relief=tk.FLAT,
            bd=0
        )
        self.password_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Button container
        button_frame = tk.Frame(login_frame, bg="#1E1A1A")
        button_frame.place(x=20, y=190, width=360, height=70)
        
        # Create rounded login button using direct tkinter button with styling
        def create_button(parent, text, command, x, y, width, height, bg_color, fg_color, hover_bg, hover_fg):
            button = tk.Button(
                parent,
                text=text,
                command=command,
                font=self.button_font,
                bg=bg_color,
                fg=fg_color,
                activebackground=hover_bg,
                activeforeground=hover_fg,
                bd=0,
                relief=tk.FLAT,
                cursor="hand2",
                padx=10,
                pady=10
            )
            button.place(x=x, y=y, width=width, height=height)
            
            # Round the corners
            button.update()
            button_width = button.winfo_width()
            button_height = button.winfo_height()
            
            # Create a rounded rectangle on a canvas and place it on top of the button
            radius = 15  # Corner radius
            
            def create_round_button_frame():
                canvas = tk.Canvas(parent, width=button_width, height=button_height, bg=parent["bg"], highlightthickness=0)
                canvas.place(x=x, y=y)
                
                # Draw rounded rectangle with given colors
                create_rounded_rect(canvas, 0, 0, button_width, button_height, radius=radius, fill=bg_color, outline=bg_color)
                
                # Add text
                canvas.create_text(button_width/2, button_height/2, text=text, fill=fg_color, font=self.button_font)
                
                # Bind events
                def on_click(e):
                    command()
                
                def on_enter(e):
                    canvas.delete("all")
                    create_rounded_rect(canvas, 0, 0, button_width, button_height, radius=radius, fill=hover_bg, outline=hover_bg)
                    canvas.create_text(button_width/2, button_height/2, text=text, fill=hover_fg, font=self.button_font)
                
                def on_leave(e):
                    canvas.delete("all")
                    create_rounded_rect(canvas, 0, 0, button_width, button_height, radius=radius, fill=bg_color, outline=bg_color)
                    canvas.create_text(button_width/2, button_height/2, text=text, fill=fg_color, font=self.button_font)
                
                canvas.bind("<Button-1>", on_click)
                canvas.bind("<Enter>", on_enter)
                canvas.bind("<Leave>", on_leave)
                
                return canvas
            
            # Hide the actual button and return the canvas
            button.place_forget()
            return create_round_button_frame()
        
        # Create sign in button
        login_button = create_button(
            button_frame, 
            "SIGN IN", 
            self.login, 
            0, 
            0, 
            170, 
            45, 
            "#C41E3A", 
            "#ffffff", 
            "#D42E4A", 
            "#ffffff"
        )
        
        # Create register button
        register_button = create_button(
            button_frame, 
            "CREATE ACCOUNT", 
            self.register, 
            190, 
            0, 
            170, 
            45, 
            "#1E1A1A", 
            "#C41E3A", 
            "#2C2222", 
            "#C41E3A"
        )
        
        # Add a border to the register button (since it's outlined style)
        register_button.create_rectangle(1, 1, 169, 44, outline="#C41E3A", width=2, fill="")
        
        # Exit button (subtle, in corner)
        exit_button = tk.Button(
            self.root, 
            text="×", 
            font=("Helvetica", 16, "bold"), 
            command=self.root.destroy, 
            bg="#0F0A0A", 
            fg="#7f8c8d", 
            activebackground="#0F0A0A", 
            activeforeground="#C41E3A", 
            bd=0,
            relief=tk.FLAT,
            cursor="hand2"
        )
        exit_button.place(x=screen_width-50, y=20)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg="#0F0A0A")
        footer_frame.place(relx=0.5, rely=0.95, anchor=tk.CENTER)
        
        footer_label = tk.Label(
            footer_frame, 
            text="© 2025 BLIZZARD ENTERTAINMENT", 
            font=("Helvetica", 8), 
            bg="#0F0A0A", 
            fg="#7f8c8d"
        )
        footer_label.pack()
        
        # Keyboard bindings
        self.root.bind("<Escape>", lambda event: self.root.destroy())
        self.root.bind("<Return>", lambda event: self.login())
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == "" or password == "":
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        success, data = self.Socket.login(username, password)
        if success:
            # Configure the messagebox style for success
            self.root.option_add('*Dialog.msg.font', 'Helvetica 12')
            self.root.option_add('*Dialog.msg.background', '#121212')
            self.root.option_add('*Dialog.msg.foreground', '#e0e0e0')
            
            messagebox.showinfo("Success", f"Welcome back to Sanctuary, {username}")
            self.data = data
            # Here you would typically launch the game or go to the next screen
            self.root.destroy()  # For demo purposes, just close the window
        else:
            if data == '1':
                messagebox.showerror("Error", "Invalid username or password")
            else:
                messagebox.showerror("Error", data)
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == "" or password == "":
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        success, data = self.Socket.register(username, password)
        if not success:
            messagebox.showerror("Error", data)
            return
        
        self.data = data
        
        messagebox.showinfo("Success", f"Account created for {username}. Enter Sanctuary if you dare.")
        self.root.destroy()