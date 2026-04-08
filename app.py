from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/acc')
def account():
    return render_template('account.html')

if __name__ == '__main__':
    app.run(debug=True)