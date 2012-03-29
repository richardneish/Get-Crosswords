from flask import Flask, session, redirect, url_for, escape, request

app = Flask(__name__)

@app.route('/')
def index():
  if 'username' in session:
    return render_template('index')
  return redirect(url_for('login'))

@app.route('/login')
def login():
  if request.method == 'POST':
    if authenticate(request.form['username'], request.form['password']):
      session['username'] = request.form['username']
      return redirect(url_for('index'))
    error = True
  return render_template('login', error)

@app.route('/logout')
def logout():
  session.pop('username', None)
  return redirect(url_for('index'))

app.secret_key = '\x9e \xd6*\x88\xf6\xc4\xaa\xb9!cl\xbd\xf5~\x88W\x90v\xa9\x9ez\xf7m'

if __name__ == '__main__':
   app.run(host='0.0.0.0', debug=True)
