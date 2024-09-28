
import tkinter as tk
from tkinter import Label, Entry, Button, Frame, messagebox
import cv2
from PIL import Image, ImageTk
import mysql.connector
import numpy as np
import face_recognition



# Function to open the registration form
def open_registration_form():
    register_window = tk.Toplevel(root)
    register_window.title("Register New User")
    register_window.geometry("400x600")

    # Labels and Entries for user details
    Label(register_window, text="Registration Form", font=("Arial", 16)).pack(pady=10)

    labels = ["Name", "Father's Name", "CNIC", "Age", "Mobile Number", "Email", "Address", "Role", "Health Conditions"]
    entries = {}
    for label in labels:
        Label(register_window, text=label).pack(anchor="w", padx=10)
        entry = Entry(register_window)
        entry.pack(fill="x", padx=10)
        entries[label] = entry

    # Frame for Camera Capture
    camera_frame = Frame(register_window)
    camera_frame.pack(pady=10)

    Label(camera_frame, text="Capture Image").pack(anchor="center")

    camera_panel = Label(camera_frame)
    camera_panel.pack()

    def show_camera_in_register():
        cap = cv2.VideoCapture(0)

        # Set camera resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 100)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 80)

        def update_frame_register():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame, (100, 100))  # Resize for display
                img = Image.fromarray(frame_resized)
                imgtk = ImageTk.PhotoImage(image=img)
                camera_panel.imgtk = imgtk
                camera_panel.config(image=imgtk)
                camera_panel.after(10, update_frame_register)

        update_frame_register()

    Button(camera_frame, text="Start Camera", command=show_camera_in_register).pack(pady=10)

    # Capture Image Button and Storage
    captured_image = None

    def capture_image():
        nonlocal captured_image
        ret, frame = cv2.VideoCapture(0).read()
        if ret:
            captured_image = frame
            Label(register_window, text="Image Captured!", fg="green").pack(pady=5)

    Button(camera_frame, text="Capture Image", command=capture_image).pack(pady=10)

    # Submit button
    def submit_registration():
        # Validate entries
        for label, entry in entries.items():
            if entry.get() == "":
                messagebox.showerror("Input Error", f"{label} cannot be empty!")
                return

        # Get user input values
        name = entries["Name"].get()
        father_name = entries["Father's Name"].get()
        cnic = entries["CNIC"].get()
        age = int(entries["Age"].get())
        mobile = entries["Mobile Number"].get()
        email = entries["Email"].get()
        address = entries["Address"].get()
        role = entries["Role"].get()
        health_conditions = entries["Health Conditions"].get()

        # Convert image to bytes (for saving in database)
        if captured_image is not None:
            _, img_encoded = cv2.imencode('.jpg', captured_image)
            img_bytes = img_encoded.tobytes()

            # Connect to MySQL database
            try:
                connection = mysql.connector.connect(
                    host="localhost",  # Change this to your host
                    user="root",       # Change this to your MySQL username
                    password="",       # Change this to your MySQL password
                    database="users"  # Change this to your MySQL database name
                )

                cursor = connection.cursor()

                # SQL query to insert data into MySQL
                query = """
                INSERT INTO users (name, father_name, cnic, age, mobile_number, email, address, role, health_conditions, image)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (name, father_name, cnic, age, mobile, email, address, role, health_conditions, img_bytes)

                cursor.execute(query, values)
                connection.commit()

                messagebox.showinfo("Success", "Registration Completed!")
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error: {err}")
            finally:
                # Close the database connection
                cursor.close()
                connection.close()
        else:
            messagebox.showwarning("Image Error", "No Image Captured!")

    Button(register_window, text="Submit", command=submit_registration).pack(pady=20)


# Function to show camera feed
def show_camera():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 150)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 150)
    def check_in_database(face_encoding):
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="users"
        )
        cursor = connection.cursor()

        cursor.execute("SELECT id, name, father_name, cnic, age, mobile_number, email, address, role, health_conditions, image FROM users")
        users = cursor.fetchall()

        for user in users:
            user_id, name, father_name, cnic, age, mobile_number, email, address, role, health_conditions, image_blob = user

            np_img = np.frombuffer(image_blob, np.uint8)
            stored_image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

            stored_image_rgb = cv2.cvtColor(stored_image, cv2.COLOR_BGR2RGB)
            stored_face_encodings = face_recognition.face_encodings(stored_image_rgb)

            if len(stored_face_encodings) > 0:
                stored_face_encoding = stored_face_encodings[0]
                results = face_recognition.compare_faces([stored_face_encoding], face_encoding)

                if results[0]:
                    return {
                        "name": name,
                        "father_name": father_name,
                        "cnic": cnic,
                        "age": age,
                        "mobile_number": mobile_number,
                        "email": email,
                        "address": address,
                        "role": role,
                        "health_conditions": health_conditions
                    }

        return None

    def update_frame():
        _, frame = cap.read()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_panel.imgtk = imgtk
        camera_panel.config(image=imgtk)

        face_locations = face_recognition.face_locations(frame_rgb)
        for top, left, bottom, right in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]
            user_details = check_in_database(face_encoding)

            if user_details:
                info_text = f"""
                Name: {user_details['name']}
                Father's Name: {user_details['father_name']}
                CNIC: {user_details['cnic']}
                Age: {user_details['age']}
                Mobile: {user_details['mobile_number']}
                Email: {user_details['email']}
                Address: {user_details['address']}
                Role: {user_details['role']}
                Health Conditions: {user_details['health_conditions']}
                """
                user_info_label.config(text=info_text)
            else:
                user_info_label.config(text="User not found!")

        camera_panel.after(30, update_frame)  # Check every second

    update_frame()


# Main App Window
root = tk.Tk()
root.title("BioPanel")
root.geometry("800x600")


# Camera Panel
camera_panel = Label(root)
camera_panel.pack(side="top", fill="both", expand=True)
show_camera()

# Bottom Frame to hold buttons and details
bottom_frame = Frame(root)
bottom_frame.pack(side="bottom", fill="x")

# New Register Button
register_button = Button(bottom_frame, text="Register a new Person?", command=open_registration_form)
register_button.pack(side="left", padx=10, pady=20)

# Details Panel
user_info_label = Label(root, text="", font=("Arial", 12), justify="left")
user_info_label.pack(side="bottom", fill="x", pady=20)

root.mainloop()