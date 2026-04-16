# Zylo 🛒

Zylo is an **ongoing e-commerce platform** where users can buy and sell products through a single unified account. The application is built using Django (Python) for the backend, MySQL as the database, and HTML, CSS, and JavaScript for the frontend. 

---

## 🔑 Features

- 🧍‍♂️ **User Registration & Login**
- 🛍️ **Browse & Buy Products** from registered sellers
- 💼 **Dual Role System** – A user can also become a seller
- 📦 **Seller Dashboard** – Manage product listings and inventory
- 🔒 **Secure Authentication System**

---

## 🛠️ Tech Stack

| Layer       | Technology           |
|-------------|----------------------|
| 💻 Frontend | HTML, CSS, JavaScript |
| 🧠 Backend  | Python, Django        |
| 🗄️ Database | MySQL                |

---

## 🚧 Project Status

🔨 This is a **work in progress (60%)**, and new features are being added actively. Contributions and feedback are welcome!

---

## ⚙️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kishore-83096/Zylo.git
   cd Zylo
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL database connection in `settings.py`**

5. **Run migrations and start the server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

