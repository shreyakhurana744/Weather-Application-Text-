import tkinter as tk
from tkinter import messagebox, Toplevel, ttk
import requests
import json
import mysql.connector
from datetime import datetime

# --- 1. Database Management Class ---
class DatabaseManager:
    """Handles all interaction with the MySQL database."""
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.db = None
        self.cursor = None
        self._connect_and_setup()

    def _connect_and_setup(self):
        """Connects to the database and ensures the table exists."""
        try:
            # 1. Connect to MySQL (without specifying the database first)
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            # 💡 FIX 1: Use a buffered cursor for the initial setup
            cursor = conn.cursor(buffered=True) 

            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            conn.commit()
            
            # Close initial connection and reconnect with the database selected
            cursor.close()
            conn.close()

            # 2. Reconnect with the database selected
            self.db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            # 💡 FIX 2: Use a buffered cursor for the main application connection
            self.cursor = self.db.cursor(buffered=True) 

            # Create weather_history table if it doesn't exist
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    city VARCHAR(255) NOT NULL,
                    country VARCHAR(10),
                    temperature_celsius DECIMAL(5, 2),
                    description VARCHAR(255),
                    humidity_percent INT,
                    wind_speed_ms DECIMAL(5, 2),
                    pressure_hpa INT,
                    timestamp DATETIME
                )
            """)
            self.db.commit()
            print("Database and table setup successful.")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Could not connect to MySQL: {err}\n"
                                 "Please ensure MySQL is running and update credentials in the code.")
            # Set db to None so the application knows the connection failed
            self.db = None

    def save_weather_data(self, city, country, temp, description, humidity, wind_speed, pressure):
        """Saves the fetched weather data into the history table."""
        if not self.db or not self.cursor:
            return # Skip if connection or cursor failed

        sql = ("INSERT INTO weather_history "
               "(city, country, temperature_celsius, description, humidity_percent, wind_speed_ms, pressure_hpa, timestamp) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
        
        now = datetime.now()
        values = (city, country, temp, description, humidity, wind_speed, pressure, now)
        
        try:
            self.cursor.execute(sql, values)
            self.db.commit()
            print(f"Data saved for {city}.")
        except mysql.connector.Error as err:
            print(f"Error saving data: {err}")

    def get_history(self):
        """Retrieves all weather history records."""
        if not self.db or not self.cursor:
            return [] # Return empty list if connection or cursor failed

        try:
            self.cursor.execute("SELECT city, country, temperature_celsius, description, timestamp FROM weather_history ORDER BY timestamp DESC LIMIT 50")
            # The buffered=True ensures this call reliably fetches all results
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error retrieving history: {err}")
            return []

    def close(self):
        """Closes the database connection."""
        if self.db:
            self.db.close()
            print("Database connection closed.")


# --- 2. Main Weather Application Class (No changes needed here, keeping your improved UI/logic) ---
class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Application")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#E0F7FA")
        
        # --- IMPORTANT: MySQL Configuration (Change These!) ---
        self.db_host = "localhost" 
        self.db_user = "root" 
        self.db_password = "Rajesh@26" # ⬅️ Ensure this password is correct
        self.db_name = "weather_db"
        
        # Initialize Database Manager
        self.db_manager = DatabaseManager(self.db_host, self.db_user, self.db_password, self.db_name)
        
        # API key (free tier from OpenWeatherMap)
        self.api_key = "a98239cf440debb229a38f4ed1d8c4eb" 
        
        self.create_widgets()
        
    def create_widgets(self):
        # ... (Your existing create_widgets method is complete) ...
        # Title Label
        title_label = tk.Label(
            self.root,
            text="🌤️ Weather App",
            font=("Inter", 24, "bold"),
            bg="#E0F7FA",
            fg="#006064"
        )
        title_label.pack(pady=20)
        
        # City Entry Frame
        entry_frame = tk.Frame(self.root, bg="#E0F7FA")
        entry_frame.pack(pady=10)
        
        city_label = tk.Label(
            entry_frame,
            text="Enter City:",
            font=("Inter", 12),
            bg="#E0F7FA"
        )
        city_label.pack(side=tk.LEFT, padx=5)
        
        self.city_entry = tk.Entry(
            entry_frame,
            font=("Inter", 12),
            width=25,
            bd=2,
            relief=tk.FLAT
        )
        self.city_entry.pack(side=tk.LEFT, padx=5)
        
        # Search and History Buttons Frame
        button_frame = tk.Frame(self.root, bg="#E0F7FA")
        button_frame.pack(pady=10)
        
        # Search Button
        search_button = tk.Button(
            button_frame,
            text="Get Weather",
            font=("Inter", 12, "bold"),
            bg="#009688",
            fg="white",
            command=self.get_weather,
            cursor="hand2",
            width=15,
            relief=tk.RAISED
        )
        search_button.pack(side=tk.LEFT, padx=10)
        
        # History Button
        history_button = tk.Button(
            button_frame,
            text="View History",
            font=("Inter", 12, "bold"),
            bg="#4FC3F7",
            fg="#000000",
            command=self.view_history,
            cursor="hand2",
            width=15,
            relief=tk.RAISED
        )
        history_button.pack(side=tk.LEFT, padx=10)

        
        # Weather Information Frame
        self.info_frame = tk.Frame(self.root, bg="#FFFFFF", relief=tk.GROOVE, bd=5)
        self.info_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)
        
        # Weather Labels
        self.city_name_label = tk.Label(
            self.info_frame,
            text="City: --",
            font=("Inter", 16, "bold"),
            bg="#FFFFFF"
        )
        self.city_name_label.pack(pady=10)
        
        self.temp_label = tk.Label(
            self.info_frame,
            text="Temperature: --",
            font=("Inter", 14),
            bg="#FFFFFF"
        )
        self.temp_label.pack(pady=5)
        
        self.description_label = tk.Label(
            self.info_frame,
            text="Description: --",
            font=("Inter", 14),
            bg="#FFFFFF"
        )
        self.description_label.pack(pady=5)
        
        self.humidity_label = tk.Label(
            self.info_frame,
            text="Humidity: --",
            font=("Inter", 14),
            bg="#FFFFFF"
        )
        self.humidity_label.pack(pady=5)
        
        self.wind_label = tk.Label(
            self.info_frame,
            text="Wind Speed: --",
            font=("Inter", 14),
            bg="#FFFFFF"
        )
        self.wind_label.pack(pady=5)
        
        self.pressure_label = tk.Label(
            self.info_frame,
            text="Pressure: --",
            font=("Inter", 14),
            bg="#FFFFFF"
        )
        self.pressure_label.pack(pady=5)
    
    def get_weather(self):
        """Fetches weather data from the API and saves it to the database."""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name!")
            return
        
        # API URL
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
        
        try:
            # Make API request
            response = requests.get(url)
            data = response.json()
            
            # Check if city was found
            if data.get("cod") == 200:
                self.display_weather(data)
                
                # --- Database Integration: Save Data ---
                self.db_manager.save_weather_data(
                    city=data["name"],
                    country=data["sys"].get("country", "N/A"),
                    temp=data["main"]["temp"],
                    description=data["weather"][0]["description"],
                    humidity=data["main"]["humidity"],
                    wind_speed=data["wind"]["speed"],
                    pressure=data["main"]["pressure"]
                )
                
            else:
                messagebox.showerror("Error", f"City not found: {city}")
                self.clear_weather_info()
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", "Unable to fetch weather data.\nCheck your internet connection.")
            print(f"API Error: {e}")
        except KeyError:
            messagebox.showerror("Error", "Invalid API response. Check your API key or data structure.")
    
    def display_weather(self, data):
        """Updates the Tkinter labels with the fetched weather information."""
        city_name = data["name"]
        country = data["sys"].get("country", "N/A")
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        pressure = data["main"]["pressure"]
        
        # Update labels
        self.city_name_label.config(text=f"City: {city_name}, {country}")
        self.temp_label.config(text=f"Temperature: {temp:.1f}°C")
        self.description_label.config(text=f"Description: {description.capitalize()}")
        self.humidity_label.config(text=f"Humidity: {humidity}%")
        self.wind_label.config(text=f"Wind Speed: {wind_speed:.1f} m/s")
        self.pressure_label.config(text=f"Pressure: {pressure} hPa")

    def clear_weather_info(self):
        """Clears all weather labels."""
        self.city_name_label.config(text="City: --")
        self.temp_label.config(text="Temperature: --")
        self.description_label.config(text="Description: --")
        self.humidity_label.config(text="Humidity: --")
        self.wind_label.config(text="Wind Speed: --")
        self.pressure_label.config(text="Wind Speed: --")
        self.pressure_label.config(text="Pressure: --")

    def view_history(self):
        """Opens a new window to display the weather search history from MySQL."""
        history_data = self.db_manager.get_history()
        
        if not history_data:
            messagebox.showinfo("History", "No search history found or database connection failed.")
            return

        # Create new Toplevel window
        history_window = Toplevel(self.root)
        history_window.title("Search History (Last 50 Records)")
        history_window.geometry("600x400")
        history_window.configure(bg="#F5F5F5")

        # Create a Treeview (table)
        tree = ttk.Treeview(
            history_window, 
            columns=("City", "Country", "Temp", "Description", "Time"), 
            show='headings'
        )
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Define column headings and widths
        tree.heading("City", text="City")
        tree.heading("Country", text="Country")
        tree.heading("Temp", text="Temp")
        tree.heading("Description", text="Description")
        tree.heading("Time", text="Time")
        
        tree.column("City", width=120, anchor=tk.CENTER)
        tree.column("Country", width=60, anchor=tk.CENTER)
        tree.column("Temp", width=60, anchor=tk.CENTER)
        tree.column("Description", width=180, anchor=tk.W)
        tree.column("Time", width=150, anchor=tk.CENTER)

        # Insert data into the Treeview
        for row in history_data:
            city, country, temp, description, timestamp = row
            
            # Format data for display
            formatted_temp = f"{temp:.1f}°C"
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M')
            
            tree.insert('', tk.END, values=(city, country, formatted_temp, description.capitalize(), formatted_time))

# --- 3. Main Execution ---
def main():
    root = tk.Tk()
    app = WeatherApp(root)
    
    # Ensure the database connection is closed when the app window is closed
    def on_closing():
        if app.db_manager.db:
            app.db_manager.close()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()