# PenPersona

PenPersona is a web app that analyzes a photo of your handwriting and predicts personality traits using graphology rules.

Your slant, spacing and pen pressure are turned into a simple personality profile, such as Confident, Expressive, Independent, Organized, Warm or Reserved. Each result comes with a short, easy-to-read explanation, so you can see what your handwriting says about you.

## How it works
1. You upload a photo of your handwriting.
2. OpenCV extracts features like slant, spacing and line patterns.
3. Rules map those features to personality traits.
4. The Gemini API reads and helps interpret the handwriting.
5. The result is shown on the web page.

## Tech stack
Python, Flask, OpenCV, Gemini API, HTML, CSS, JavaScript

## Setup
1. Clone the repo and open the folder.
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Create a file `backend/.env` and add your own key: `GEMINI_API_KEY=your_key_here`
4. Run the app: `python backend/app.py`

## Team
- Pranjali
- Varad
- Ritwik
- Prachi

## Note
Graphology is not a proven science. This project is for learning and fun, not for real decisions about people.
