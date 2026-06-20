from flask import Flask
app=Flask(__name__)
app.config['SECRET_KEY']='change-me'
@app.route('/')
def home(): return 'Password Manager Running'
if __name__=='__main__': app.run(debug=True)