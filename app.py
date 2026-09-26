import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # reads variables from .env into the environment

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Read SECRET_KEY from environment; fall back to a dev-only default if missing
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key-do-not-use-in-production')

db = SQLAlchemy(app)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Needed for flash messages to work (Flask signs the session cookie with this).
# We'll move this to an environment variable properly in a later step.
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'

db = SQLAlchemy(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"


@app.route('/')
def home():
    status_filter = request.args.get('status', 'all')

    if status_filter == 'completed':
        tasks = Task.query.filter_by(completed=True).order_by(Task.created_at.desc()).all()
    elif status_filter == 'pending':
        tasks = Task.query.filter_by(completed=False).order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.order_by(Task.created_at.desc()).all()

    total_count = Task.query.count()
    completed_count = Task.query.filter_by(completed=True).count()
    pending_count = Task.query.filter_by(completed=False).count()

    return render_template(
        'index.html',
        tasks=tasks,
        total_count=total_count,
        completed_count=completed_count,
        pending_count=pending_count,
        status_filter=status_filter
    )


@app.route('/about')
def about():
    return "This is a task manager built with Flask."


@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()

        # Validate: title must not be empty
        if not title:
            flash('Title is required.')
            return redirect(url_for('add_task'))

        # Convert the due_date string (e.g. "2026-09-30") into a Python date object
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

        new_task = Task(title=title, description=description, due_date=due_date)
        db.session.add(new_task)
        db.session.commit()

        flash('Task added successfully!')
        return redirect(url_for('home'))

    # GET request: just show the empty form
    return render_template('add_task.html')


@app.route('/toggle/<int:task_id>')
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()

    flash('Task updated!')
    return redirect(url_for('home'))
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()

    flash('Task deleted.')
    return redirect(url_for('home'))
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()

        if not title:
            flash('Title is required.')
            return redirect(url_for('edit_task', task_id=task.id))

        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

        task.title = title
        task.description = description
        task.due_date = due_date
        # Checkbox inputs only appear in form data when checked, so we check for its presence
        task.completed = 'completed' in request.form

        db.session.commit()

        flash('Task updated successfully!')
        return redirect(url_for('home'))

    # GET request: show the form pre-filled with this task's current data
    return render_template('edit_task.html', task=task)
if __name__ == '__main__':
    app.run(debug=True)