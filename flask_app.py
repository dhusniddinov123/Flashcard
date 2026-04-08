from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_app.db'
db = SQLAlchemy(app)

# Database Models
class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cards = db.relationship('Card', backref='collection', lazy=True, cascade="all, delete-orphan")

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.String(200), nullable=False)
    back = db.Column(db.String(200), nullable=False)
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
        
        # Get card data from form (fronts and backs)
        fronts = request.form.getlist('front[]')
        backs = request.form.getlist('back[]')
        
        for f, b in zip(fronts, backs):
            if f and b:
                card = Card(front=f, back=b, collection_id=new_collection.id)
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
    return jsonify([{"front": c.front, "back": c.back} for c in cards])

@app.route('/edit/<int:deck_id>', methods=['GET', 'POST'])
def edit_deck(deck_id):
    deck = Collection.query.get_or_404(deck_id)
    
    if request.method == 'POST':
        # 1. Update Deck Name
        deck.name = request.form.get('deck_name')
        
        # 2. Remove old cards (Simplest way to update)
        Card.query.filter_by(collection_id=deck.id).delete()
        
        # 3. Add updated cards from the form
        fronts = request.form.getlist('front[]')
        backs = request.form.getlist('back[]')
        
        for f, b in zip(fronts, backs):
            if f.strip() and b.strip():
                new_card = Card(front=f, back=b, collection_id=deck.id)
                db.session.add(new_card)
        
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit.html', deck=deck)
if __name__ == '__main__':
    app.run(debug=True)