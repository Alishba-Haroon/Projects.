from flask import Flask, render_template, request
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load dataset
bank = pd.read_csv('Dataset_Banking_chatbot.csv', encoding='cp1252')

# Prepare formatted responses
bank["ResponseFormatted"] = bank.apply(lambda row: f"Query: {row['Query']}\nAnswer: {row['Response']}", axis=1)

# Load embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")

# Precompute embeddings
queries = bank["Query"].tolist()
query_embeddings = embeddings.embed_documents(queries)

@app.route('/', methods=['GET', 'POST'])
def index():
    conversation = []

    if request.method == 'POST':
        user_input = request.form['query']
        user_embedding = embeddings.embed_query(user_input)

        # Find most similar query
        similarities = cosine_similarity([user_embedding], query_embeddings)[0]
        best_match_index = similarities.argmax()
        bot_response = bank.iloc[best_match_index]["Response"]

        # Just show the current user-bot exchange
        conversation = [('User', user_input), ('Bot', bot_response)]

    return render_template('index.html', conversation=conversation)

if __name__ == '__main__':
    app.run(debug=True)
