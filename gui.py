import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import DatabaseManager, CSV_EXPORT_FILENAME # Import CSV_EXPORT_FILENAME

# --- Configuration (Dark Mode Theme) ---
BG_DARK = "#1a1a2e"         # Deep Navy Blue Background (Container)
BG_PRIMARY = "#16213e"      # Richer blue for main content
FG_LIGHT = "#eeeeee"        # Lighter text for better contrast
ACCENT_BLUE = "#0f3460"     # Deep Royal Blue accent
SIDEBAR_COLOR = "#0d0d1a"   # Very dark navy for the sidebar
SUCCESS_GREEN = "#4ade80"   # Modern vibrant green
WARNING_RED = "#f87171"     # Soft red for warnings
ADMIN_COLOR = "#fbbf24"     # Amber gold for admin

# Fonts
FONT_STYLE = ("Inter", 12)
HEADER_FONT_STYLE = ("Inter", 16, "bold")
TITLE_FONT_STYLE = ("Inter", 28, "bold")
BUTTON_FONT_STYLE = ("Inter", 14, "bold")


# --- DAA ALGORITHM IMPLEMENTATION: Merge Sort O(N log N) ---
def merge_sort(arr, key_index, ascending=True):
    """
    Implements the Merge Sort algorithm, a comparison sort based on the 
    divide-and-conquer paradigm, ensuring O(N log N) time complexity.
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]

    left = merge_sort(left, key_index, ascending)
    right = merge_sort(right, key_index, ascending)

    return merge(left, right, key_index, ascending)

def merge(left, right, key_index, ascending):
    """Merges two sorted lists."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        left_val = left[i][key_index]
        right_val = right[j][key_index]

        # Convert amount to float for correct numeric comparison if required
        if key_index in (2, 3): 
            try:
                left_val = float(left_val)
                right_val = float(right_val)
            except (ValueError, TypeError):
                pass 
        
        if ascending:
            if left_val < right_val:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        else: # Descending
            if left_val > right_val:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result
# --- END DAA ALGORITHM IMPLEMENTATION ---


class BankingApp(tk.Tk):
    """
    Main application window and controller. 
    Manages frames (views) and holds the DatabaseManager instance.
    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Banking System")
        self.geometry("1000x650")
        self.resizable(False, False)
        
        self.config(bg=BG_DARK)

        try:
            # Initialize the database connection manager
            self.db = DatabaseManager()
        except ConnectionError as e:
            messagebox.showerror("Database Startup Error", str(e))
            self.quit()
        
        # --- Apply Modern Tkinter Styles for Improved UX ---
        style = ttk.Style(self)
        style.theme_use('clam')
        
        # General Styles
        style.configure('.', font=FONT_STYLE, background=BG_PRIMARY, foreground=FG_LIGHT)
        style.configure('TFrame', background=BG_PRIMARY)
        style.configure('TLabel', background=BG_PRIMARY, foreground=FG_LIGHT)
        style.configure('TEntry', fieldbackground=BG_DARK, foreground=FG_LIGHT, borderwidth=1, relief="flat", padding=5)
        
        # Primary Button style (Blue)
        style.configure('T.TButton', font=BUTTON_FONT_STYLE, padding=[20, 10], 
                        background=ACCENT_BLUE, foreground=FG_LIGHT, borderwidth=0, relief="flat")
        style.map('T.TButton', background=[('active', '#1a3d7a')], foreground=[('active', FG_LIGHT)])

        # Action Button style (Green for transactions/confirmations)
        style.configure('Action.TButton', font=BUTTON_FONT_STYLE, padding=[15, 8], 
                        background=SUCCESS_GREEN, foreground=BG_DARK, borderwidth=0, relief="flat")
        style.map('Action.TButton', background=[('active', '#3bbd60')], foreground=[('active', BG_DARK)])
        
        # Logout/Admin Button styles
        style.configure('Logout.TButton', font=BUTTON_FONT_STYLE, padding=[15, 8], 
                        background=WARNING_RED, foreground=FG_LIGHT, borderwidth=0, relief="flat")
        style.map('Logout.TButton', background=[('active', '#e55c5c')], foreground=[('active', FG_LIGHT)])
        
        style.configure('Admin.TButton', font=BUTTON_FONT_STYLE, padding=[15, 8], 
                        background=ADMIN_COLOR, foreground=BG_DARK, borderwidth=0, relief="flat")
        style.map('Admin.TButton', background=[('active', '#f5a623')], foreground=[('active', BG_DARK)])
        
        # Treeview (Statement) styling - Improved readability
        style.configure("Treeview.Heading", font=FONT_STYLE, background=SIDEBAR_COLOR, foreground=FG_LIGHT, padding=5)
        style.configure("Treeview", background=BG_PRIMARY, foreground=FG_LIGHT, fieldbackground=BG_PRIMARY, rowheight=25)
        
        self.current_user_id = None
        self.current_username = None
        self.is_admin = False
        # Cache for user's sorted statements fetched at login
        self.sorted_statements = None
        # Cache for admin-sorted accounts
        self.sorted_accounts = None
        # Cache for admin full-system sorted transactions
        self.sorted_all_transactions = None

        # Container setup for frames
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # Define all available frames
        for F in (WelcomeFrame, RegisterFrame, LoginFrame, AdminLoginFrame, UserHomeFrame, AdminDashboardFrame):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("WelcomeFrame")

    def show_frame(self, page_name):
        """Raises the requested frame to the front."""
        frame = self.frames[page_name]
        frame.tkraise()
        # Reset specific frame content if needed on display
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def login(self, user_id, username, is_admin=False):
        """Sets the current user state after successful login."""
        self.current_user_id = user_id
        self.current_username = username
        self.is_admin = is_admin
        # Pre-fetch and sort statements for faster display in the statement view
        if not is_admin and user_id is not None:
            try:
                self.prefetch_and_sort_statements(user_id)
            except Exception:
                # Non-fatal: continue without cached statements
                self.sorted_statements = None

        # For admin logins, prefetch and sort the accounts by username
        if is_admin:
            try:
                self.prefetch_and_sort_accounts()
            except Exception:
                self.sorted_accounts = None

        # Also prefetch and sort the full system transaction history for admin
        if is_admin:
            try:
                self.prefetch_and_sort_all_transactions()
            except Exception:
                self.sorted_all_transactions = None

        if is_admin:
            self.show_frame("AdminDashboardFrame")
        else:
            self.show_frame("UserHomeFrame")

    def prefetch_and_sort_statements(self, user_id):
        """Fetches transaction history for the given user and stores a sorted copy.

        Uses the file-local merge_sort to order by timestamp (index 0) newest-first.
        """
        history = self.db.get_transaction_history(user_id)
        if not history:
            self.sorted_statements = []
            return

        try:
            # Sort by timestamp (index 0), descending (newest first)
            self.sorted_statements = merge_sort(history, key_index=0, ascending=False)
        except Exception:
            # If merge_sort fails, fall back to the DB-provided order
            self.sorted_statements = history

    def prefetch_and_sort_accounts(self):
        """Fetches all accounts and stores a sorted copy ordered by username (index 1).

        Uses the merge_sort implemented in this file to perform the sort (ascending A->Z).
        """
        all_accounts = self.db.get_all_accounts_summary()
        if not all_accounts:
            self.sorted_accounts = []
            return

        try:
            # account tuple format: (id, username, balance) -> sort by username at index 1
            self.sorted_accounts = merge_sort(all_accounts, key_index=1, ascending=True)
        except Exception:
            # Fallback to DB order
            self.sorted_accounts = all_accounts

    def prefetch_and_sort_all_transactions(self):
        """Fetches the entire transaction history (all users) and stores a sorted copy ordered by timestamp (newest-first).

        Uses the merge_sort implemented in this file to perform the sort (descending newest-first).
        """
        history = self.db.get_all_transactions()
        if not history:
            self.sorted_all_transactions = []
            return

        try:
            # history tuple format: (timestamp, username, type, amount, description)
            # sort by timestamp at index 0, descending (newest first)
            self.sorted_all_transactions = merge_sort(history, key_index=0, ascending=False)
        except Exception:
            # Fallback to DB-provided order
            self.sorted_all_transactions = history

    def logout(self):
        """Resets user state and returns to welcome screen."""
        self.current_user_id = None
        self.current_username = None
        self.is_admin = False
        # Clear cached statements on logout
        self.sorted_statements = None
        # Clear admin caches
        self.sorted_accounts = None
        self.sorted_all_transactions = None
        self.show_frame("WelcomeFrame")


# --- Base Frame for Content Pages (Sidebar Integration) ---

class BaseContentFrame(tk.Frame):
    """
    Base class for frames that use the sidebar (UserHomeFrame, AdminDashboardFrame).
    It sets up the left sidebar and the main content area.
    """
    def __init__(self, parent, controller, sidebar_class):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller

        # 1. Grid setup: Sidebar on the left (25%), Content on the right (75%)
        self.grid_columnconfigure(0, weight=1, minsize=200)  # Sidebar
        self.grid_columnconfigure(1, weight=3)              # Main Content
        self.grid_rowconfigure(0, weight=1)

        # 2. Sidebar Container
        self.sidebar = sidebar_class(self, controller)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 3. Main Content Container
        self.content_container = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=20)
        self.content_container.grid(row=0, column=1, sticky="nsew")

        # Initialize the sub-frames dictionary
        self.sub_frames = {}
        self.current_sub_frame = None
        
    def add_sub_frame(self, name, frame_class):
        """Creates and places a sub-frame inside the content container."""
        frame = frame_class(self.content_container, self.controller)
        self.sub_frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        return frame

    def show_sub_frame(self, page_name):
        """Raises the requested sub-frame and calls its on_show method."""
        frame = self.sub_frames.get(page_name)
        if frame:
            if self.current_sub_frame and hasattr(self.current_sub_frame, 'on_hide'):
                self.current_sub_frame.on_hide() # Optional: Hook to clear fields on switch
                
            frame.tkraise()
            if hasattr(frame, 'on_show'):
                frame.on_show()
            self.current_sub_frame = frame
            
    def on_show(self):
        """Called when the whole main frame is displayed."""
        self.sidebar.on_show()
        # Default to showing the first item in the sidebar
        first_frame_name = list(self.sub_frames.keys())[0]
        self.show_sub_frame(first_frame_name)


# --- Sidebar Definitions (Unchanged) ---

class UserSidebar(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=SIDEBAR_COLOR)
        self.controller = controller
        
        self.columnconfigure(0, weight=1)
        
        tk.Label(self, text="Bank App", font=HEADER_FONT_STYLE, bg=SIDEBAR_COLOR, fg=ACCENT_BLUE).grid(row=0, column=0, pady=(30, 20), sticky="n")

        self.buttons = {
            "Balance": {"row": 1, "target": "AccountSummaryFrame", "icon": "🏠"},
            "Deposit": {"row": 2, "target": "DepositFrame", "icon": "💰"},
            "Withdraw": {"row": 3, "target": "WithdrawFrame", "icon": "💸"},
            "Transfer": {"row": 4, "target": "TransferFrame", "icon": "📤"},
            "Statement": {"row": 5, "target": "StatementFrame", "icon": "📜"},
        }

        for name, data in self.buttons.items():
            ttk.Button(self, text=f"{data['icon']} {name}", style='T.TButton',
                       command=lambda t=data['target']: parent.show_sub_frame(t)) \
                       .grid(row=data['row'], column=0, padx=10, pady=5, sticky="ew")

        ttk.Button(self, text="Logout", style='Logout.TButton', command=controller.logout) \
            .grid(row=10, column=0, padx=10, pady=(100, 20), sticky="s")

    def on_show(self):
        pass


class AdminSidebar(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=SIDEBAR_COLOR)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        
        tk.Label(self, text="Admin Console", font=HEADER_FONT_STYLE, bg=SIDEBAR_COLOR, fg=ADMIN_COLOR).grid(row=0, column=0, pady=(30, 20), sticky="n")

        self.buttons = {
            "Dashboard": {"row": 1, "target": "AdminOverviewFrame", "icon": "📊"},
            "Accounts": {"row": 2, "target": "AdminAccountsFrame", "icon": "👤"},
            "Full Statement": {"row": 3, "target": "AdminStatementFrame", "icon": "📋"},
        }
        
        for name, data in self.buttons.items():
            ttk.Button(self, text=f"{data['icon']} {name}", style='Admin.TButton',
                       command=lambda t=data['target']: parent.show_sub_frame(t)) \
                       .grid(row=data['row'], column=0, padx=10, pady=5, sticky="ew")

        ttk.Button(self, text="Admin Logout", style='Logout.TButton', command=controller.logout) \
            .grid(row=10, column=0, padx=10, pady=(100, 20), sticky="s")

    def on_show(self):
        pass


# --- Top-Level User/Admin Frames (Unchanged) ---

class UserHomeFrame(BaseContentFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, UserSidebar)
        
        self.add_sub_frame("AccountSummaryFrame", AccountSummaryFrame)
        self.add_sub_frame("DepositFrame", DepositFrame)
        self.add_sub_frame("WithdrawFrame", WithdrawFrame)
        self.add_sub_frame("TransferFrame", TransferFrame)
        self.add_sub_frame("StatementFrame", StatementFrame)

    def on_show(self):
        super().on_show()
        

class AdminDashboardFrame(BaseContentFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, AdminSidebar)
        
        self.add_sub_frame("AdminOverviewFrame", AdminOverviewFrame)
        self.add_sub_frame("AdminAccountsFrame", AdminAccountsFrame)
        self.add_sub_frame("AdminStatementFrame", AdminStatementFrame)


# --- Authentication Frames (Unchanged) ---
class WelcomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_DARK)
        self.controller = controller
        
        # Center the content
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)

        tk.Label(self, text="Secure Banking", font=TITLE_FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT).grid(row=1, column=0, columnspan=2, pady=(0, 10))
        tk.Label(self, text="Login or Register to access your account.", font=HEADER_FONT_STYLE, bg=BG_DARK, fg=ACCENT_BLUE).grid(row=2, column=0, columnspan=2, pady=(10, 40))
        
        login_btn = ttk.Button(self, text="User Login", style='T.TButton',
                               command=lambda: controller.show_frame("LoginFrame"))
        login_btn.grid(row=3, column=0, padx=20, pady=10, ipadx=40, sticky="e")

        register_btn = ttk.Button(self, text="Register", style='T.TButton',
                                  command=lambda: controller.show_frame("RegisterFrame"))
        register_btn.grid(row=3, column=1, padx=20, pady=10, ipadx=40, sticky="w")
        
        admin_login_btn = ttk.Button(self, text="Admin Login", style='Admin.TButton',
                                     command=lambda: controller.show_frame("AdminLoginFrame"))
        admin_login_btn.grid(row=4, column=0, columnspan=2, pady=(20, 10), ipadx=40)
        
        tk.Label(self, text="Powered by Python Tkinter", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT).grid(row=5, column=0, columnspan=2, pady=(80, 0))


class RegisterFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_DARK)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(7, weight=1)

        tk.Label(self, text="Create New Account", font=TITLE_FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT).grid(row=1, column=0, columnspan=2, pady=(40, 30))

        # Input fields...
        tk.Label(self, text="Username:", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=2, column=0, padx=50, pady=10, sticky="w")
        self.username_entry = ttk.Entry(self, width=40)
        self.username_entry.grid(row=2, column=1, padx=50, pady=10, sticky="ew")

        tk.Label(self, text="Password:", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=3, column=0, padx=50, pady=10, sticky="w")
        self.password_entry = ttk.Entry(self, show="*", width=40)
        self.password_entry.grid(row=3, column=1, padx=50, pady=10, sticky="ew")
        
        tk.Label(self, text="Initial Deposit ($):", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=4, column=0, padx=50, pady=10, sticky="w")
        self.deposit_entry = ttk.Entry(self, width=40)
        self.deposit_entry.grid(row=4, column=1, padx=50, pady=10, sticky="ew")
        self.deposit_entry.insert(0, "0.00")
        
        # Buttons
        register_btn = ttk.Button(self, text="Register", style='T.TButton', command=self.register_user)
        register_btn.grid(row=5, column=0, columnspan=2, pady=(30, 10), ipadx=50)

        back_btn = ttk.Button(self, text="Back to Welcome", style='T.TButton', command=lambda: controller.show_frame("WelcomeFrame"))
        back_btn.grid(row=6, column=0, columnspan=2, pady=10, ipadx=50)

    def register_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        initial_deposit = self.deposit_entry.get()

        if not username or not password or not initial_deposit:
            messagebox.showerror("Error", "All fields are required.")
            return

        result = self.controller.db.create_account(username, password, initial_deposit)

        if result is True:
            messagebox.showinfo("Success", "Account created successfully! You can now log in.")
            self.clear_fields()
            self.controller.show_frame("LoginFrame")
        else:
            messagebox.showerror("Registration Failed", result)

    def clear_fields(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.deposit_entry.delete(0, tk.END)
        self.deposit_entry.insert(0, "0.00")

    def on_show(self):
        self.clear_fields()


class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_DARK)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)
        
        tk.Label(self, text="Account Login", font=TITLE_FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT).grid(row=1, column=0, columnspan=2, pady=(40, 30))

        # Input fields...
        tk.Label(self, text="Username:", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=2, column=0, padx=50, pady=10, sticky="w")
        self.username_entry = ttk.Entry(self, width=40)
        self.username_entry.grid(row=2, column=1, padx=50, pady=10, sticky="ew")

        tk.Label(self, text="Password:", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=3, column=0, padx=50, pady=10, sticky="w")
        self.password_entry = ttk.Entry(self, show="*", width=40)
        self.password_entry.grid(row=3, column=1, padx=50, pady=10, sticky="ew")

        # Buttons
        login_btn = ttk.Button(self, text="Login", style='T.TButton', command=self.login_user)
        login_btn.grid(row=4, column=0, columnspan=2, pady=(30, 10), ipadx=50)

        back_btn = ttk.Button(self, text="Back to Welcome", style='T.TButton', command=lambda: controller.show_frame("WelcomeFrame"))
        back_btn.grid(row=5, column=0, columnspan=2, pady=10, ipadx=50)

    def login_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        result = self.controller.db.check_credentials(username, password)

        if result:
            user_id, uname = result
            messagebox.showinfo("Success", f"Welcome, {uname}!")
            self.clear_fields()
            self.controller.login(user_id, uname)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def clear_fields(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def on_show(self):
        self.clear_fields()


class AdminLoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_DARK)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)
        
        tk.Label(self, text="Admin Login", font=TITLE_FONT_STYLE, bg=BG_DARK, fg=ADMIN_COLOR).grid(row=1, column=0, columnspan=2, pady=(40, 30))
        tk.Label(self, text="Access System Management Tools", font=HEADER_FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT).grid(row=2, column=0, columnspan=2, pady=(0, 20))

        # Input fields...
        tk.Label(self, text="Admin Username:", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=3, column=0, padx=50, pady=10, sticky="w")
        self.username_entry = ttk.Entry(self, width=40)
        self.username_entry.grid(row=3, column=1, padx=50, pady=10, sticky="ew")

        tk.Label(self, text="Admin Password:", font=FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT, anchor="w").grid(row=4, column=0, padx=50, pady=10, sticky="w")
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=4, column=1, padx=50, pady=10, sticky="ew")

        # Buttons
        login_btn = ttk.Button(self, text="Admin Login", style='Admin.TButton', command=self.login_admin)
        login_btn.grid(row=5, column=0, columnspan=2, pady=(30, 10), ipadx=50)

        back_btn = ttk.Button(self, text="Back to Welcome", style='T.TButton', command=lambda: controller.show_frame("WelcomeFrame"))
        back_btn.grid(row=6, column=0, columnspan=2, pady=10, ipadx=50)

    def login_admin(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if self.controller.db.check_admin_credentials(username, password):
            messagebox.showinfo("Success", f"Welcome, Admin {username}!")
            self.clear_fields()
            self.controller.login(user_id=0, username=username, is_admin=True) 
        else:
            messagebox.showerror("Login Failed", "Invalid admin credentials.")

    def clear_fields(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def on_show(self):
        self.clear_fields()

# --- User Sub-Frames (Unchanged) ---
class AccountSummaryFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller

        tk.Label(self, text="Account Overview", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=(10, 20))

        # Balance display
        self.balance_frame = tk.Frame(self, bg=ACCENT_BLUE, padx=40, pady=30, relief="flat")
        self.balance_frame.pack(pady=20, padx=50, fill="x")
        
        tk.Label(self.balance_frame, text="Current Balance:", font=HEADER_FONT_STYLE, 
                 bg=ACCENT_BLUE, fg=BG_DARK).pack()
                 
        self.balance_label = tk.Label(self.balance_frame, text="$0.00", font=("Inter", 48, "bold"), 
                                      bg=ACCENT_BLUE, fg=BG_DARK)
        self.balance_label.pack(pady=10)

        tk.Label(self, text="Quick Actions:", font=HEADER_FONT_STYLE, bg=BG_PRIMARY, fg=ACCENT_BLUE).pack(pady=(30, 10))

        # Quick action buttons
        actions_frame = tk.Frame(self, bg=BG_PRIMARY)
        actions_frame.pack(pady=10)
        
        # Link quick actions to sidebar functionality
        ttk.Button(actions_frame, text="Deposit", style='Action.TButton', command=lambda: self.controller.frames["UserHomeFrame"].show_sub_frame("DepositFrame")) \
            .grid(row=0, column=0, padx=10, pady=10, ipadx=10)
        ttk.Button(actions_frame, text="Withdraw", style='Action.TButton', command=lambda: self.controller.frames["UserHomeFrame"].show_sub_frame("WithdrawFrame")) \
            .grid(row=0, column=1, padx=10, pady=10, ipadx=10)
        ttk.Button(actions_frame, text="Transfer", style='Action.TButton', command=lambda: self.controller.frames["UserHomeFrame"].show_sub_frame("TransferFrame")) \
            .grid(row=0, column=2, padx=10, pady=10, ipadx=10)

    def on_show(self):
        self.update_balance_display()

    def update_balance_display(self):
        """Fetches and displays the updated balance."""
        if not self.controller.current_user_id:
            return
            
        balance = self.controller.db.get_balance(self.controller.current_user_id)
        self.balance_label.config(text=f"${balance:,.2f}")


class DepositFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller
        
        deposit_container = tk.Frame(self, bg=BG_PRIMARY, padx=50, pady=30)
        deposit_container.pack(fill="both", expand=True)

        tk.Label(deposit_container, text="Deposit Money", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=SUCCESS_GREEN).pack(pady=(10, 30))

        tk.Label(deposit_container, text="Amount ($):", font=HEADER_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=5)
        self.amount_entry = ttk.Entry(deposit_container, width=30, justify='center')
        self.amount_entry.pack(pady=10, ipadx=20)

        deposit_btn = ttk.Button(deposit_container, text="Confirm Deposit", style='Action.TButton', command=self.handle_deposit)
        deposit_btn.pack(pady=30, ipadx=50)

    def handle_deposit(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Deposit amount must be positive.")
            return

        user_id = self.controller.current_user_id
        
        try:
            self.controller.db.update_balance(user_id, amount)
            self.controller.db.record_transaction(user_id, 'Deposit', amount)

            # Update summary and switch back to it
            self.controller.frames["UserHomeFrame"].sub_frames["AccountSummaryFrame"].update_balance_display()
            messagebox.showinfo("Success", f"Successfully deposited ${amount:,.2f}.")
            self.on_hide()
            self.controller.frames["UserHomeFrame"].show_sub_frame("AccountSummaryFrame")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def on_show(self):
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.focus_set()
        
    def on_hide(self):
        self.amount_entry.delete(0, tk.END)


class WithdrawFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller
        
        withdraw_container = tk.Frame(self, bg=BG_PRIMARY, padx=50, pady=30)
        withdraw_container.pack(fill="both", expand=True)

        tk.Label(withdraw_container, text="Withdraw Money", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=WARNING_RED).pack(pady=(10, 30))

        tk.Label(withdraw_container, text="Amount ($):", font=HEADER_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=5)
        self.amount_entry = ttk.Entry(withdraw_container, width=30, justify='center')
        self.amount_entry.pack(pady=10, ipadx=20)

        withdraw_btn = ttk.Button(withdraw_container, text="Confirm Withdrawal", style='Action.TButton', command=self.handle_withdraw)
        withdraw_btn.pack(pady=30, ipadx=50)

    def handle_withdraw(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Withdrawal amount must be positive.")
            return

        user_id = self.controller.current_user_id
        current_balance = self.controller.db.get_balance(user_id)

        if amount > current_balance:
            messagebox.showerror("Insufficient Funds", f"You only have ${current_balance:,.2f} in your account.")
            return

        try:
            self.controller.db.update_balance(user_id, -amount)
            self.controller.db.record_transaction(user_id, 'Withdrawal', -amount)

            self.controller.frames["UserHomeFrame"].sub_frames["AccountSummaryFrame"].update_balance_display()
            messagebox.showinfo("Success", f"Successfully withdrew ${amount:,.2f}.")
            self.on_hide()
            self.controller.frames["UserHomeFrame"].show_sub_frame("AccountSummaryFrame")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def on_show(self):
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.focus_set()

    def on_hide(self):
        self.amount_entry.delete(0, tk.END)


class TransferFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller
        
        transfer_container = tk.Frame(self, bg=BG_PRIMARY, padx=50, pady=30)
        transfer_container.pack(fill="both", expand=True)

        tk.Label(transfer_container, text="Transfer Funds", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=ACCENT_BLUE).pack(pady=(10, 30))

        tk.Label(transfer_container, text="Recipient Username:", font=HEADER_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=5)
        self.recipient_entry = ttk.Entry(transfer_container, width=30, justify='center')
        self.recipient_entry.pack(pady=5, ipadx=20)
        
        tk.Label(transfer_container, text="Amount ($):", font=HEADER_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=5)
        self.amount_entry = ttk.Entry(transfer_container, width=30, justify='center')
        self.amount_entry.pack(pady=10, ipadx=20)

        transfer_btn = ttk.Button(transfer_container, text="Confirm Transfer", style='Action.TButton', command=self.handle_transfer)
        transfer_btn.pack(pady=30, ipadx=50)

    def handle_transfer(self):
        recipient_username = self.recipient_entry.get().strip()
        
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Transfer amount must be positive.")
            return

        sender_id = self.controller.current_user_id
        sender_username = self.controller.current_username
        
        recipient_id = self.controller.db.get_account_id_by_username(recipient_username)
        
        if recipient_id is None:
            messagebox.showerror("Transfer Failed", f"Recipient account '{recipient_username}' not found.")
            return
            
        if sender_id == recipient_id:
            messagebox.showerror("Transfer Failed", "Cannot transfer funds to your own account.")
            return

        current_balance = self.controller.db.get_balance(sender_id)

        if amount > current_balance:
            messagebox.showerror("Insufficient Funds", f"You only have ${current_balance:,.2f} in your account.")
            return

        try:
            self.controller.db.update_balance(sender_id, -amount)
            self.controller.db.update_balance(recipient_id, amount)
            self.controller.db.record_transaction(sender_id, 'Transfer (Out)', -amount, f"Transfer to {recipient_username}")
            self.controller.db.record_transaction(recipient_id, 'Transfer (In)', amount, f"Transfer from {sender_username}")

            self.controller.frames["UserHomeFrame"].sub_frames["AccountSummaryFrame"].update_balance_display()
            messagebox.showinfo("Success", f"Successfully transferred ${amount:,.2f} to {recipient_username}.")
            self.on_hide()
            self.controller.frames["UserHomeFrame"].show_sub_frame("AccountSummaryFrame")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during transfer: {e}")

    def on_show(self):
        self.clear_fields()
        self.recipient_entry.focus_set()

    def on_hide(self):
        self.clear_fields()
        
    def clear_fields(self):
        self.recipient_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)


class StatementFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller
        
        statement_container = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=20)
        statement_container.pack(fill="both", expand=True)
        
        tk.Label(statement_container, text="Account Statement", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=(10, 20))
        
        # Treeview setup
        columns = ("Timestamp", "Type", "Amount", "Description")
        self.statement_tree = ttk.Treeview(statement_container, columns=columns, show="headings", height=15)
        
        self.statement_tree.heading("Timestamp", text="Date/Time")
        self.statement_tree.heading("Type", text="Type")
        self.statement_tree.heading("Amount", text="Amount")
        self.statement_tree.heading("Description", text="Description")
        
        self.statement_tree.column("Timestamp", width=140, anchor="center")
        self.statement_tree.column("Type", width=100, anchor="center")
        self.statement_tree.column("Amount", width=100, anchor="e")
        self.statement_tree.column("Description", width=200, anchor="w")
        
        vsb = ttk.Scrollbar(statement_container, orient="vertical", command=self.statement_tree.yview)
        vsb.pack(side="right", fill="y")
        self.statement_tree.configure(yscrollcommand=vsb.set)
        
        self.statement_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
    def on_show(self):
        # Clear existing entries
        for item in self.statement_tree.get_children():
            self.statement_tree.delete(item)

        user_id = self.controller.current_user_id
        if not user_id:
            return
            
        # 1. Use cached sorted statements if available (populated at login), otherwise fetch and sort now.
        if getattr(self.controller, 'sorted_statements', None) is not None:
            sorted_history = self.controller.sorted_statements
        else:
            # Fetch the raw transaction history
            history = self.controller.db.get_transaction_history(user_id)

            if not history:
                self.statement_tree.insert("", "end", values=("---", "No Transactions Yet", "---", "---"))
                return

            # Sort the history using the existing merge_sort algorithm by timestamp (index 0)
            try:
                sorted_history = merge_sort(history, key_index=0, ascending=False)
            except Exception as e:
                # Fallback in case of a sorting error
                print(f"Error during merge sort: {e}")
                messagebox.showwarning("Sort Error", "Could not sort statements. Displaying unsorted data.")
                sorted_history = history


        # 3. Populate the Treeview with the sorted data
        for record in sorted_history:
            # record is: (timestamp, type, amount, description)
            timestamp, type, amount, description = record
            
            # Format amount with sign and currency and determine tag for color
            # Use the 'amount' column (index 2) which is a float from the DB manager.
            if amount > 0:
                formatted_amount = f"${amount:,.2f}"
                tag = 'green' # Positive transaction (Deposit, Transfer In)
            else:
                formatted_amount = f"-${abs(amount):,.2f}"
                tag = 'red' # Negative transaction (Withdrawal, Transfer Out)

            # Insert the record into the Treeview
            self.statement_tree.insert("", "end", values=(timestamp, type, formatted_amount, description), tags=(tag,))
            
        # Configure the color tags for the rows
        try:
            self.statement_tree.tag_configure('green', foreground=SUCCESS_GREEN)
            self.statement_tree.tag_configure('red', foreground=WARNING_RED)
        except Exception:
            pass


# --- Admin Sub-Frames (Modified AdminStatementFrame) ---

class AdminOverviewFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller

        tk.Label(self, text="Admin Dashboard", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=ADMIN_COLOR).pack(pady=(10, 20))
        
        tk.Label(self, text="System Statistics (WIP)", font=HEADER_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=10)
        
        stats_frame = tk.Frame(self, bg=BG_DARK, padx=30, pady=30)
        stats_frame.pack(pady=20, padx=50, fill="x")
        
        self.total_accounts_label = tk.Label(stats_frame, text="Total Accounts: N/A", font=HEADER_FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT)
        self.total_accounts_label.pack(pady=5)
        
        self.total_balance_label = tk.Label(stats_frame, text="Total Balance: N/A", font=HEADER_FONT_STYLE, bg=BG_DARK, fg=FG_LIGHT)
        self.total_balance_label.pack(pady=5)
        
        tk.Label(stats_frame, text="View 'Accounts' and 'Full Statement' for detailed data.", font=FONT_STYLE, bg=BG_DARK, fg=ACCENT_BLUE).pack(pady=20)

    def on_show(self):
        all_accounts = self.controller.db.get_all_accounts_summary()
        
        total_accounts = len(all_accounts)
        total_balance = sum(balance for _, _, balance in all_accounts)
        
        self.total_accounts_label.config(text=f"Total Accounts: {total_accounts}")
        self.total_balance_label.config(text=f"Total System Balance: ${total_balance:,.2f}")


class AdminAccountsFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller
        
        accounts_container = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=20)
        accounts_container.pack(fill="both", expand=True)
        
        tk.Label(accounts_container, text="All Client Accounts", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=(10, 20))
        
        columns = ("ID", "Username", "Balance")
        self.accounts_tree = ttk.Treeview(accounts_container, columns=columns, show="headings", height=15)
        
        self.accounts_tree.heading("ID", text="ID")
        self.accounts_tree.heading("Username", text="Username")
        self.accounts_tree.heading("Balance", text="Balance")
        
        self.accounts_tree.column("ID", width=50, anchor="center")
        self.accounts_tree.column("Username", width=150, anchor="center")
        self.accounts_tree.column("Balance", width=150, anchor="e")
        
        vsb = ttk.Scrollbar(accounts_container, orient="vertical", command=self.accounts_tree.yview)
        vsb.pack(side="right", fill="y")
        self.accounts_tree.configure(yscrollcommand=vsb.set)
        
        self.accounts_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
    def on_show(self):
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)

        # Use cached sorted accounts if available (populated at admin login), otherwise fetch and sort now
        if getattr(self.controller, 'sorted_accounts', None) is not None:
            all_accounts = self.controller.sorted_accounts
        else:
            all_accounts = self.controller.db.get_all_accounts_summary()
            try:
                # Ensure alphabetical order by username (index 1)
                all_accounts = merge_sort(all_accounts, key_index=1, ascending=True)
            except Exception:
                # Fall back to DB order
                pass

        if not all_accounts:
            self.accounts_tree.insert("", "end", values=("---", "No User Accounts Found", "---"))
            return

        for acc_id, username, balance in all_accounts:
            formatted_balance = f"${balance:,.2f}"
            self.accounts_tree.insert("", "end", values=(acc_id, username, formatted_balance))


class AdminStatementFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_PRIMARY)
        self.controller = controller
        
        statement_container = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=20)
        statement_container.pack(fill="both", expand=True)
        
        tk.Label(statement_container, text="Full System Transaction History", font=TITLE_FONT_STYLE, bg=BG_PRIMARY, fg=FG_LIGHT).pack(pady=(10, 20))
        
        # Frame for the Treeview and Scrollbar
        tree_frame = tk.Frame(statement_container, bg=BG_PRIMARY)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview setup
        columns = ("Timestamp", "User", "Type", "Amount", "Description")
        self.statement_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.statement_tree.heading("Timestamp", text="Date/Time")
        self.statement_tree.heading("User", text="User")
        self.statement_tree.heading("Type", text="Type")
        self.statement_tree.heading("Amount", text="Amount")
        self.statement_tree.heading("Description", text="Description")
        
        self.statement_tree.column("Timestamp", width=120, anchor="center")
        self.statement_tree.column("User", width=100, anchor="center")
        self.statement_tree.column("Type", width=100, anchor="center")
        self.statement_tree.column("Amount", width=90, anchor="e")
        self.statement_tree.column("Description", width=200, anchor="w")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.statement_tree.yview)
        vsb.pack(side="right", fill="y")
        self.statement_tree.configure(yscrollcommand=vsb.set)
        
        self.statement_tree.pack(side="left", fill="both", expand=True)

        # Export Button (New Feature)
        ttk.Button(statement_container, text="Export to CSV 📄", style='Admin.TButton', command=self.export_data) \
            .pack(pady=10, ipadx=50)

    def export_data(self):
        """Calls the database function to export data and handles the success/failure message."""
        try:
            # The database function handles writing the file with a predefined name
            filename = self.controller.db.export_all_transactions_to_csv()
            
            if filename:
                messagebox.showinfo("Export Successful", 
                                    f"Successfully exported all transactions to:\n{filename}")
            else:
                messagebox.showwarning("Export Warning", "No transaction data found to export.")

        except IOError as e:
            messagebox.showerror("Export Failed", f"A file system error occurred: {e}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An unexpected error occurred during export: {e}")
        
    def on_show(self):
        """Refreshes the full transaction history for all users."""
        for item in self.statement_tree.get_children():
            self.statement_tree.delete(item)
            
        # Use cached sorted full-history if available (populated at admin login), otherwise fetch and sort now
        if getattr(self.controller, 'sorted_all_transactions', None) is not None:
            sorted_history = self.controller.sorted_all_transactions
        else:
            history = self.controller.db.get_all_transactions()

            if not history:
                self.statement_tree.insert("", "end", values=("---", "---", "No System Transactions", "---", "---"))
                return

            try:
                sorted_history = merge_sort(history, key_index=0, ascending=False)
            except Exception:
                sorted_history = history

        for record in sorted_history:
            timestamp, username, type, amount, description = record
            
            if amount > 0:
                formatted_amount = f"${amount:,.2f}"
                tag = 'green'
            else:
                formatted_amount = f"-${abs(amount):,.2f}"
                tag = 'red'

            self.statement_tree.insert("", "end", values=(timestamp, username, type, formatted_amount, description), tags=(tag,))
            
        try:
            self.statement_tree.tag_configure('green', foreground=SUCCESS_GREEN)
            self.statement_tree.tag_configure('red', foreground=WARNING_RED)
        except Exception:
            pass