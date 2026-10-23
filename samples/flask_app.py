import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_production_key_12345'
DEBUG = True


def get_db():
    conn = sqlite3.connect('database.db')
    return conn


@app.route('/users')
def get_user():
    user_id = request.args.get('id')
    cursor = get_db().cursor()
    # SQL injection vulnerability
    cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    user = cursor.fetchone()
    return jsonify(user)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
