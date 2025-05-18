from flask import Flask, render_template, jsonify
from voice_assistant import handle_voice_command

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/listen', methods=['GET'])
def listen():
    response = handle_voice_command()
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
