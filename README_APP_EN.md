# **Plant Image Classification and Management App**

**This file explains how the app works in English. However, the app itself is still only available in Spanish**

This app is part of a system designed to collect, store, and label images of healthy and diseased plant leaves. It allows users to interact with the image database and perform specific tasks according to their role: **user**, **labeler**, or **administrator**.

---

## **📋 Main Features**

### **For Users:**
- Upload plant leaf images:
  - **Individual upload**: Upload a single image to the database.
  - **Bulk upload**: Upload multiple images organized in folders, by searching folders on the PC where the API is running. For Users+ only.
- Perform basic predictions using trained models*
- **Experiments**:
  - View results of existing experiments
  - Compare existing experiments
  - Create a new experiment and request its training

### **For Labelers:**
- Validate images uploaded by users.
- Review and edit labels associated with images.
- Modify existing classes in the database.

### **For Administrators:**
- Manage users:
  - Add new users.
  - Delete existing users.
  - Modify user roles (user, labeler, administrator).
- Approve model training requests.

### **Other Features:**
- User registration.
- Change the API IP address from the app.
- Change the database address.

---

## **⚙️ Requirements**

- Python 3.8 or higher.
- Flutter 3.16.7 to create the APK.
- Install project dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## **To Use the App Connected to the Main API:**
- **Basic usage:**
  - Run the `main_app.py` file:
    ```bash
    python main_app.py
    ```
  - Connect to the main API (when available).  
    If you need to change the API IP, you can do so from the app settings.

---

## **To Use the App with Your Own Local Database:**
If you want to work with your own local MongoDB database, follow these additional steps:

1. **Clone the repository:**
   ```bash
   git clone <REPOSITORY_URL>
   cd <REPOSITORY_FOLDER>
   ```

2. **Configure the local database:**
  - Make sure you have MongoDB installed and running on your machine.
  - Run the setup_bbdd.py script to initialize the database:
  ```bash
  python scripts/setup_bbdd.py
  ```

3. **Run the API:**
  - Start the API on your local machine:
  ```bash
  python main.py
  ```

4. **Change the API URL and database:**

  - From the app, change the API URL to point to your local machine (e.g., http://127.0.0.1:5001).

5. **Upload images and work with your database:**
  - Use the bulk or individual upload functionality from the app.
  - Perform validations, edits, and experiments with your local database.

## 📖 Important Notes
 - While the main server is not available, the app's features will be limited.
 - If you decide to work with your own local database, make sure to follow the steps described in the corresponding section.
 - In image prediction, if you provide the corresponding plant, it will continue to give you the probability that the prediction is correct considering all possibilities, not just those of that plant.

## 🤝 Contributions and Contact
 - If you want to contribute to app development, please open an issue or submit a pull request.
 - For questions or suggestions, contact the developer.
