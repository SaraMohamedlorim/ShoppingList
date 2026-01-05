import customtkinter as ctk
import sqlite3
import csv
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
import matplotlib.pyplot as plt

DB_NAME = "shopping_list.db"

# ------------------- DATABASE FUNCTIONS -------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity TEXT NOT NULL,
        category TEXT,
        priority TEXT,
        bought INTEGER DEFAULT 0,
        date_added TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_item(name, quantity, category, priority):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO items (name, quantity, category, priority, date_added) VALUES (?, ?, ?, ?, ?)",
                (name, quantity, category, priority, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def fetch_items():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def update_item(item_id, name, quantity, category, priority, bought):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE items SET name=?, quantity=?, category=?, priority=?, bought=? WHERE id=?",
                (name, quantity, category, priority, bought, item_id))
    conn.commit()
    conn.close()

def toggle_bought(item_id, bought):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE items SET bought=? WHERE id=?", (bought, item_id))
    conn.commit()
    conn.close()


# ------------------- MAIN APP CLASS -------------------
class ShoppingListApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🛒 Shopping List App")
        self.geometry("900x600")
        self.configure(padx=10, pady=10)
        init_db()
        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        """INPUT FRAME"""
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", pady=5)

        self.name_entry = ctk.CTkEntry(input_frame, placeholder_text="Item Name")
        self.name_entry.grid(row=0, column=0, padx=5, pady=5)

        self.quantity_entry = ctk.CTkEntry(input_frame, placeholder_text="Quantity")
        self.quantity_entry.grid(row=0, column=1, padx=5, pady=5)

        self.category_entry = ctk.CTkEntry(input_frame, placeholder_text="Category")
        self.category_entry.grid(row=0, column=2, padx=5, pady=5)

        self.priority_entry = ctk.CTkEntry(input_frame, placeholder_text="Priority (High/Low)")
        self.priority_entry.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(input_frame, text="➕ Add Item", command=self.add_item_action).grid(row=0, column=4, padx=5)

        """SEARCH BAR"""
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(search_frame, text="🔎 Search:").pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter name or category")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_frame, text="Search", command=self.search_items).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Show All", command=self.refresh_table).pack(side="left", padx=5)

        """TABLE"""
        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Quantity", "Category", "Priority", "Bought", "Date"), show="headings")
        for col in ("ID", "Name", "Quantity", "Category", "Priority", "Bought", "Date"):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", stretch=True)
        self.tree.pack(pady=10, fill="both", expand=True)

        """BUTTONS"""
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="🗑 Delete", command=self.delete_selected).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏ Edit", command=self.edit_selected).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✔ Toggle Bought", command=self.toggle_selected).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="💾 Export CSV", command=self.export_csv).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📊 Stats", command=self.show_stats).pack(side="left", padx=5)

    def refresh_table(self, filtered=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = filtered if filtered is not None else fetch_items()
        for r in rows:
            bought_status = "✅" if r[5] else "❌"
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], bought_status, r[6]))

    def add_item_action(self):
        name = self.name_entry.get().strip()
        quantity = self.quantity_entry.get().strip()
        category = self.category_entry.get().strip()
        priority = self.priority_entry.get().strip()
        if not name or not quantity:
            messagebox.showerror("Error", "Name and Quantity are required!")
            return
        add_item(name, quantity, category, priority)
        self.refresh_table()
        self.name_entry.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self.category_entry.delete(0, "end")
        self.priority_entry.delete(0, "end")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an item to delete.")
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete?"):
            item_id = self.tree.item(selected[0])['values'][0]
            delete_item(item_id)
            self.refresh_table()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an item to edit.")
            return
        item = self.tree.item(selected[0])['values']
        EditWindow(self, item, self.refresh_table)

    def toggle_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an item to toggle bought status.")
            return
        item = self.tree.item(selected[0])['values']
        item_id, bought = item[0], item[5] == "✅"
        toggle_bought(item_id, not bought)
        self.refresh_table()

    def search_items(self):
        keyword = self.search_entry.get().strip().lower()
        rows = fetch_items()
        filtered = [r for r in rows if keyword in r[1].lower() or keyword in (r[3] or "").lower()]
        self.refresh_table(filtered)

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            rows = fetch_items()
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Quantity", "Category", "Priority", "Bought", "Date"])
                writer.writerows(rows)
            messagebox.showinfo("Success", "List exported successfully!")

    def show_stats(self):
        rows = fetch_items()
        categories = {}
        for r in rows:
            categories[r[3]] = categories.get(r[3], 0) + 1
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
        plt.title("Items by Category")
        plt.show()


# ------------------- EDIT WINDOW CLASS -------------------
class EditWindow(ctk.CTkToplevel):
    def __init__(self, parent, item, refresh_callback):
        super().__init__(parent)
        self.title("✏ Edit Item")
        self.geometry("400x250")
        self.item_id = item[0]
        self.refresh_callback = refresh_callback

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Name")
        self.name_entry.insert(0, item[1])
        self.name_entry.pack(pady=5)

        self.quantity_entry = ctk.CTkEntry(self, placeholder_text="Quantity")
        self.quantity_entry.insert(0, item[2])
        self.quantity_entry.pack(pady=5)

        self.category_entry = ctk.CTkEntry(self, placeholder_text="Category")
        self.category_entry.insert(0, item[3])
        self.category_entry.pack(pady=5)

        self.priority_entry = ctk.CTkEntry(self, placeholder_text="Priority")
        self.priority_entry.insert(0, item[4])
        self.priority_entry.pack(pady=5)

        self.bought_var = ctk.BooleanVar(value=item[5] == "✅")
        ctk.CTkCheckBox(self, text="Bought", variable=self.bought_var).pack(pady=5)

        ctk.CTkButton(self, text="Save", command=self.save_changes).pack(pady=10)

    def save_changes(self):
        update_item(
            self.item_id,
            self.name_entry.get().strip(),
            self.quantity_entry.get().strip(),
            self.category_entry.get().strip(),
            self.priority_entry.get().strip(),
            int(self.bought_var.get())
        )
        self.refresh_callback()
        self.destroy()


if __name__ == "__main__":
    app = ShoppingListApp()
    app.mainloop()
