from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q')
    print(f"Search query: {query}")
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')
    
if __name__ == '__main__':
    app.run(debug=True)