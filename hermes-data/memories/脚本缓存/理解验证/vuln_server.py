"""
有漏洞的 Flask 应用 — SQL注入靶场
仅用于学习 sqlmap 注入检测
"""

from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'vuln.db')

def init_db():
    # 删掉旧的重新创建
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        email TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        category TEXT
    )''')
    # 插入数据
    users = [
        (1, 'admin', 'supersecret123', 'admin@bliiot.com', 'admin'),
        (2, 'user1', 'password1', 'user1@test.com', 'user'),
        (3, 'manager', 'mgrpass456', 'manager@bliiot.com', 'manager'),
        (4, 'kali', 'hunter2', 'kali@bliiot.com', 'user'),
    ]
    c.executemany('INSERT INTO users VALUES (?,?,?,?,?)', users)
    products = [
        (1, 'ARM Edge Controller', 299.99, 'Industrial IoT'),
        (2, 'BLIIOT Gateway R40', 159.99, 'Industrial IoT'),
        (3, 'IOy Remote IO Module', 89.99, 'Remote IO'),
        (4, 'RTU5028', 199.99, 'RTU'),
    ]
    c.executemany('INSERT INTO products VALUES (?,?,?,?)', products)
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return '''<html><body>
        <h1>BLIIOT Vuln Test Server</h1>
        <p>Vulnerable endpoints:</p>
        <ul>
            <li><a href="/user?id=1">/user?id=1 (SQL注入)</a></li>
            <li><a href="/product?id=1">/product?id=1 (SQL注入)</a></li>
            <li><a href="/search?q=admin">/search?q=admin (SQL注入)</a></li>
        </ul>
    </body></html>'''

@app.route('/user')
def user():
    """有SQL注入的用户查询"""
    uid = request.args.get('id', '1')
    conn = get_db()
    try:
        query = f"SELECT id, username, email, role FROM users WHERE id = '{uid}'"
        print(f"[SQL] {query}")
        cur = conn.execute(query)
        row = cur.fetchone()
        if row:
            return f'''<html><body>
                <h1>User Profile</h1>
                <p>ID: {row['id']}</p>
                <p>Username: {row['username']}</p>
                <p>Email: {row['email']}</p>
                <p>Role: {row['role']}</p>
            </body></html>'''
        return '<html><body><h1>User not found</h1></body></html>'
    except Exception as e:
        return f'<html><body><h1>Database Error</h1><p>{str(e)}</p></body></html>'

@app.route('/product')
def product():
    """有SQL注入的产品查询"""
    pid = request.args.get('id', '1')
    conn = get_db()
    try:
        query = f"SELECT id, name, price, category FROM products WHERE id = '{pid}'"
        print(f"[SQL] {query}")
        cur = conn.execute(query)
        row = cur.fetchone()
        if row:
            return f'''<html><body>
                <h1>Product Info</h1>
                <p>ID: {row['id']}</p>
                <p>Name: {row['name']}</p>
                <p>Price: ${row['price']}</p>
                <p>Category: {row['category']}</p>
            </body></html>'''
        return '<html><body><h1>Product not found</h1></body></html>'
    except Exception as e:
        return f'<html><body><h1>Database Error</h1><p>{str(e)}</p></body></html>'

@app.route('/search')
def search():
    """有SQL注入的搜索"""
    q = request.args.get('q', '')
    conn = get_db()
    try:
        query = f"SELECT id, username, email FROM users WHERE username LIKE '%{q}%'"
        print(f"[SQL] {query}")
        cur = conn.execute(query)
        rows = cur.fetchall()
        if rows:
            items = ''.join(f'<li>{r["id"]}: {r["username"]} ({r["email"]})</li>' for r in rows)
            return f'<html><body><h1>Search Results</h1><ul>{items}</ul></body></html>'
        return '<html><body><h1>No results</h1></body></html>'
    except Exception as e:
        return f'<html><body><h1>Database Error</h1><p>{str(e)}</p></body></html>'

if __name__ == '__main__':
    print("* Vuln server running on http://127.0.0.1:5000")
    print("* Test: http://127.0.0.1:5000/user?id=1")
    print("* Test: http://127.0.0.1:5000/user?id=1' OR '1'='1")
    app.run(host='127.0.0.1', port=5000, debug=False)