import os
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Adjust path to find sibling modules if run standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sun_tracker.cities import CITIES
from sun_tracker.calculator import run_calculation
from sun_tracker.exporter import save_to_excel

class SunTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Sun Arc-Minute Tracker")
        self.geometry("600x530")
        self.minsize(550, 480)
        
        self.configure(bg="#f8f9fa")
        
        # Load icon if exists
        import sys
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_path, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
                
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configure_styles()
        
        self.last_generated_files = []
        self.create_widgets()
        
    def configure_styles(self):
        self.style.configure(".", background="#f8f9fa", foreground="#212529", font=("Segoe UI", 10))
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat", borderwidth=1)
        self.style.configure("Primary.TButton", 
                             background="#0077b6", 
                             foreground="#ffffff", 
                             font=("Segoe UI", 10, "bold"), 
                             padding=6, 
                             relief="flat")
        self.style.map("Primary.TButton",
                       background=[("active", "#0096c7"), ("disabled", "#adb5bd")],
                       foreground=[("disabled", "#6c757d")])
                       
        self.style.configure("Standard.TButton", 
                             background="#e9ecef", 
                             foreground="#212529", 
                             font=("Segoe UI", 10), 
                             padding=4, 
                             relief="flat")
        self.style.map("Standard.TButton",
                       background=[("active", "#dee2e6")])

        self.style.configure("Accent.TButton", 
                             background="#2a9d8f", 
                             foreground="#ffffff", 
                             font=("Segoe UI", 10, "bold"), 
                             padding=6, 
                             relief="flat")
        self.style.map("Accent.TButton",
                       background=[("active", "#3dbeb2"), ("disabled", "#adb5bd")],
                       foreground=[("disabled", "#6c757d")])

        self.style.configure("Custom.Horizontal.TProgressbar", 
                             troughcolor="#e9ecef", 
                             background="#0077b6", 
                             thickness=15)
                             
    def create_widgets(self):
        # 1. Header
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        title_label = ttk.Label(header_frame, 
                                text="Sun Arc-Minute Tracker", 
                                font=("Segoe UI", 16, "bold"), 
                                foreground="#0077b6",
                                background="#f8f9fa")
        title_label.pack(anchor="w")
        
        desc_label = ttk.Label(header_frame, 
                               text="Calculate the exact times of Sun's tropical longitude crossing every 1-arcminute boundary.", 
                               foreground="#6c757d",
                               background="#f8f9fa")
        desc_label.pack(anchor="w", pady=(2, 0))
        
        # 2. Form Container (Card)
        form_card = ttk.Frame(self, style="Card.TFrame")
        form_card.pack(fill="x", padx=20, pady=5)
        
        form_inner = tk.Frame(form_card, bg="#ffffff", bd=0)
        form_inner.pack(fill="both", padx=15, pady=15)
        
        # Years grid
        ttk.Label(form_inner, text="Start Year:", background="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        self.start_year_var = tk.StringVar(value=str(datetime.now().year))
        self.start_year_spin = ttk.Spinbox(form_inner, from_=1800, to=2200, textvariable=self.start_year_var, width=10)
        self.start_year_spin.grid(row=0, column=1, sticky="w", padx=(5, 20), pady=5)
        
        ttk.Label(form_inner, text="End Year:", background="#ffffff").grid(row=0, column=2, sticky="w", pady=5)
        self.end_year_var = tk.StringVar(value=str(datetime.now().year))
        self.end_year_spin = ttk.Spinbox(form_inner, from_=1800, to=2200, textvariable=self.end_year_var, width=10)
        self.end_year_spin.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        # City Dropdown
        ttk.Label(form_inner, text="City (Exact Coordinates):", background="#ffffff").grid(row=1, column=0, sticky="w", pady=8)
        self.city_var = tk.StringVar(value="Delhi")
        self.city_combo = ttk.Combobox(form_inner, textvariable=self.city_var, values=list(CITIES.keys()), state="readonly", width=12)
        self.city_combo.grid(row=1, column=1, columnspan=3, sticky="w", padx=(5, 0), pady=8)
        
        # Save directory
        ttk.Label(form_inner, text="Output Directory:", background="#ffffff").grid(row=2, column=0, sticky="w", pady=5)
        self.output_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        if not os.path.exists(self.output_dir_var.get()):
            self.output_dir_var.set(os.getcwd())
            
        self.output_dir_entry = ttk.Entry(form_inner, textvariable=self.output_dir_var, width=45)
        self.output_dir_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(5, 5), pady=5)
        
        self.browse_btn = ttk.Button(form_inner, text="Browse...", style="Standard.TButton", command=self.browse_directory)
        self.browse_btn.grid(row=2, column=3, sticky="e", pady=5)
        
        form_inner.grid_columnconfigure(2, weight=1)
        
        # 3. Actions Block
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill="x", padx=20, pady=10)
        
        self.generate_btn = ttk.Button(actions_frame, text="Generate Excel Report", style="Primary.TButton", command=self.start_generation)
        self.generate_btn.pack(side="left", padx=(0, 10))
        
        self.open_btn = ttk.Button(actions_frame, text="Open Output Folder", style="Accent.TButton", command=self.open_output_folder, state="disabled")
        self.open_btn.pack(side="left")
        
        # 4. Progress & Status
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", padx=20, pady=5)
        
        self.progress_bar = ttk.Progressbar(status_frame, style="Custom.Horizontal.TProgressbar", mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 2))
        
        self.status_var = tk.StringVar(value="Ready to generate.")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 9, "italic"), foreground="#495057")
        self.status_label.pack(anchor="w")
        
        # 5. Log Text View
        log_frame = ttk.Frame(self, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Consolas", 9), bg="#fafafa", fg="#333333", bd=0, height=7)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.log_text.yview)
        
        self.log_text.config(state="disabled")
        
    def log(self, message: str):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        
    def browse_directory(self):
        dir_path = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if dir_path:
            self.output_dir_var.set(dir_path)
            
    def open_output_folder(self):
        if self.output_dir_var.get() and os.path.exists(self.output_dir_var.get()):
            try:
                os.startfile(self.output_dir_var.get())
            except Exception as e:
                messagebox.showerror("Error", f"Could not open directory: {e}")
        else:
            messagebox.showerror("Error", "Output directory does not exist.")
            
    def start_generation(self):
        try:
            start_year = int(self.start_year_var.get())
            end_year = int(self.end_year_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers for the years.")
            return
            
        if start_year > end_year:
            messagebox.showerror("Invalid Range", "Start Year must be less than or equal to End Year.")
            return
            
        # Disable controls
        self.generate_btn.config(state="disabled")
        self.open_btn.config(state="disabled")
        self.start_year_spin.config(state="disabled")
        self.end_year_spin.config(state="disabled")
        self.city_combo.config(state="disabled")
        self.browse_btn.config(state="disabled")
        
        # Clear log
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
        self.progress_bar["value"] = 0
        
        # Start background calculation thread
        thread = threading.Thread(target=self.run_export_thread, args=(start_year, end_year))
        thread.daemon = True
        thread.start()
        
    def run_export_thread(self, start_year: int, end_year: int):
        city_name = self.city_var.get()
        output_dir = self.output_dir_var.get()
        
        self.log(f"Starting Sun Arc-Minute Tracker calculation for {start_year} to {end_year}...")
        self.log(f"Selected City: {city_name}")
        self.log(f"Saving reports to: {output_dir}")
        
        try:
            years = list(range(start_year, end_year + 1))
            total_years = len(years)
            self.last_generated_files = []
            
            for idx, year in enumerate(years):
                self.status_var.set(f"Generating year {year}...")
                
                # Progress callback inside the year calculation
                def year_progress(status_msg, pct):
                    self.status_var.set(f"[{year}] {status_msg}")
                    # Scale progress for the current year
                    overall_pct = ((idx / total_years) * 100) + ((pct / 100) * (100 / total_years))
                    self.progress_bar["value"] = overall_pct
                    self.update_idletasks()
                
                self.log(f"Scanning year {year} minute-by-minute (Skyfield + JPL)...")
                rows = run_calculation(year, city_name, progress_callback=year_progress)
                
                self.log(f"Found {len(rows):,} crossing moments in {year}.")
                
                # Format name: Sun_Delhi_2024.xlsx
                filename = f"Sun_{city_name}_{year}.xlsx"
                file_path = os.path.join(output_dir, filename)
                
                self.log(f"Writing dataset to {filename}...")
                save_to_excel(rows, file_path, year)
                self.log(f"Saved: {filename}")
                self.last_generated_files.append(file_path)
                
                # Update progress for complete year
                self.progress_bar["value"] = ((idx + 1) / total_years) * 100
                
            self.status_var.set("Generation complete!")
            self.log("All years processed successfully!")
            self.open_btn.config(state="normal")
            
            messagebox.showinfo("Success", "Excel reports generated successfully!")
            
        except Exception as e:
            self.status_var.set("Failed!")
            self.log(f"ERROR: Calculation failed: {e}")
            messagebox.showerror("Execution Failed", f"An error occurred:\n{e}")
            
        finally:
            # Re-enable UI
            self.generate_btn.config(state="normal")
            self.start_year_spin.config(state="normal")
            self.end_year_spin.config(state="normal")
            self.city_combo.config(state="normal")
            self.browse_btn.config(state="normal")

if __name__ == "__main__":
    app = SunTrackerApp()
    app.mainloop()
