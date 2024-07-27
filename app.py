from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import csv
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Flask-Session Configuration
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem-based sessions
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)

# Load MCQs from CSV
def load_mcqs(filename):
    mcqs = []
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for index, row in enumerate(reader):
            mcq = {
                'number': index + 1,  # Add question number
                'question': row['Questions'],
                'options': {
                    'A': row['A'].strip(),
                    'B': row['B'].strip(),
                    'C': row['C'].strip(),
                    'D': row['D'].strip()
                },
                'correct_option': row['Correct'].strip().upper(),  # Store correct option letter
                'subject': identify_subject(index)
            }
            mcqs.append(mcq)
    return mcqs

# Identify subject based on index
def identify_subject(index):
    if index < 68:
        return 'Biology'
    elif index < 122:
        return 'Chemistry'
    elif index < 176:
        return 'Physics'
    elif index < 194:
        return 'English'
    else:
        return 'Logical Reasoning'

# Load MCQs
mcqs = load_mcqs('mcqs.csv')

@app.route('/')
def index():
    session['start_time'] = time.time()
    session['mcq_index'] = 0
    session['answers'] = []
    session['skipped_mcqs'] = []
    session['shown_mcqs'] = set()  # Track shown MCQs
    session['scores'] = {'Biology': {'correct': 0, 'total': 68},
                         'Chemistry': {'correct': 54, 'total': 54},
                         'Physics': {'correct': 54, 'total': 54},
                         'English': {'correct': 18, 'total': 18},
                         'Logical Reasoning': {'correct': 6, 'total': 6}}
    return redirect(url_for('show_mcq'))


@app.route('/mcq')
def show_mcq():
    index = session.get('mcq_index', 0)
    skipped_mcqs = session.get('skipped_mcqs', [])
    error = session.pop('error', None)

    elapsed_time = time.time() - session['start_time']
    if elapsed_time > 600:
        return redirect(url_for('results'))

    if index >= 200:
        # Show skipped MCQs if available
        if skipped_mcqs:
            mcq_index = skipped_mcqs.pop(0)  # Get the first skipped MCQ
            mcq = mcqs[mcq_index]
            session['skipped_mcqs'] = skipped_mcqs
            session['mcq_index'] = mcq_index  # Set index to the current skipped MCQ
        else:
            return redirect(url_for('results'))
    else:
        if index < len(mcqs):
            mcq = mcqs[index]
            session['shown_mcqs'].add(index)
        else:
            mcq = None

    return render_template('mcq.html', mcq=mcq, elapsed_time=elapsed_time, error=error)





@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    answer = request.form.get('answer')
    if not answer:
        session['error'] = 'Please select an option before proceeding.'
        return redirect(url_for('show_mcq'))

    index = session.get('mcq_index', 0)
    if index < len(mcqs):
        mcq = mcqs[index]
        correct_option = mcq['correct_option']
        user_answer = answer.strip().upper()

        if user_answer == correct_option:
            subject = mcq['subject']
            session['scores'][subject]['correct'] += 1

        # Remove from skipped MCQs if present
        skipped_mcqs = session.get('skipped_mcqs', [])
        if index in skipped_mcqs:
            skipped_mcqs.remove(index)
            session['skipped_mcqs'] = skipped_mcqs

        session['answers'].append((mcq, user_answer))
        session['mcq_index'] += 1

    return redirect(url_for('show_mcq'))


@app.route('/skip_mcq', methods=['POST'])
def skip_mcq():
    index = session.get('mcq_index', 0)
    if index < len(mcqs):
        skipped_mcqs = session.get('skipped_mcqs', [])
        if index not in skipped_mcqs:  # Ensure not to duplicate
            skipped_mcqs.append(index)  # Store only the index
            session['skipped_mcqs'] = skipped_mcqs
        session['mcq_index'] += 1

    return redirect(url_for('show_mcq'))

@app.route('/results')
def results():
    scores = session.get('scores', {})
    total_correct = sum(score['correct'] for score in scores.values())
    total_questions = sum(score['total'] for score in scores.values())
    answers = session.get('answers', [])
    return render_template('results.html', scores=scores, total_correct=total_correct, total_questions=total_questions, answers=answers, mcqs=mcqs)

if __name__ == '__main__':
    app.run(debug=True)
