from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database Setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'study_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Relationship to cards: if deck is deleted, cards are deleted too
    cards = db.relationship('Card', backref='collection', lazy=True, cascade="all, delete-orphan")

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(200), nullable=False)      
    tone = db.Column(db.String(100))                     
    translation = db.Column(db.String(200), nullable=False) 
    example = db.Column(db.Text)                      
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)

# Create the database file
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def dashboard():
    collections = Collection.query.all()
    return render_template('dashboard.html', collections=collections)

@app.route('/create', methods=['GET', 'POST'])
def create_deck():
    if request.method == 'POST':
        deck_name = request.form.get('deck_name')
        new_collection = Collection(name=deck_name)
        db.session.add(new_collection)
        db.session.commit()
        
        words = request.form.getlist('word[]')
        tones = request.form.getlist('tone[]')
        translations = request.form.getlist('translation[]')
        examples = request.form.getlist('example[]')
        
        for w, t, tr, ex in zip(words, tones, translations, examples):
            if w.strip():
                card = Card(word=w, tone=t, translation=tr, example=ex, collection_id=new_collection.id)
                db.session.add(card)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create.html')

@app.route('/study/<int:deck_id>')
def study_view(deck_id):
    deck = Collection.query.get_or_404(deck_id)
    return render_template('study.html', deck=deck)

@app.route('/api/get_cards/<int:deck_id>')
def get_cards_api(deck_id):
    cards = Card.query.filter_by(collection_id=deck_id).all()
    return jsonify([{
        "word": c.word, 
        "tone": c.tone, 
        "translation": c.translation, 
        "example": c.example
    } for c in cards])

@app.route('/edit/<int:deck_id>', methods=['GET', 'POST'])
def edit_deck(deck_id):
    deck = Collection.query.get_or_404(deck_id)
    if request.method == 'POST':
        deck.name = request.form.get('deck_name')
        
        # Remove existing cards
        Card.query.filter_by(collection_id=deck.id).delete()
        db.session.flush()
        
        # Add updated list of cards
        words = request.form.getlist('word[]')
        tones = request.form.getlist('tone[]')
        translations = request.form.getlist('translation[]')
        examples = request.form.getlist('example[]')
        
        for w, t, tr, ex in zip(words, tones, translations, examples):
            if w.strip():
                new_card = Card(
                    word=w.strip(), 
                    tone=t.strip() if t else None, 
                    translation=tr.strip(), 
                    example=ex.strip() if ex else None, 
                    collection_id=deck.id
                )
                db.session.add(new_card)
                
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit.html', deck=deck)

@app.route('/delete/<int:deck_id>')
def delete_deck(deck_id):
    deck = Collection.query.get_or_404(deck_id)
    db.session.delete(deck)
    db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)