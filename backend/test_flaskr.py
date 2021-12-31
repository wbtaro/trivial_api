import os
import subprocess
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
  """This class represents the trivia test case"""

  def setUp(self):
    """Define test variables and initialize app."""
    self.app = create_app()
    self.client = self.app.test_client
    database_name = "trivia_test"
    username = 'student'
    password = 'student'
    url = 'localhost:5432'
    database_path = "postgresql://{}:{}@{}/{}".format(
      username,
      password,
      url,
      database_name
    )
    setup_db(self.app, database_path)

    # binds the app to the current context
    with self.app.app_context():
      self.db = SQLAlchemy()
      self.db.init_app(self.app)
      # create all tables
      self.db.create_all()

    # set question for delete test
    self.question_for_delete_test = Question(
      question='test',
      answer='test',
      difficulty=1,
      category=1
    )
    self.question_for_delete_test.insert()

  def tearDown(self):
    """Executed after reach test"""
    self.question_for_delete_test.delete()
    pass

  """
  TODO
  Write at least one test for each test for successful operation and for expected errors.
  """

  def test_get_categories(self):
    res = self.client().get('/categories')
    data = json.loads(res.data)

    self.assertEqual(res.status_code, 200)
    self.assertTrue(data['success'])
    self.assertTrue(data['total_categories'])
    self.assertTrue(data['categories'])

  def test_get_questions_first_page(self):
    res = self.client().get('/questions')
    data = json.loads(res.data)

    self.assertEqual(res.status_code, 200)
    self.assertTrue(data['questions'])
    self.assertEqual(len(data['questions']), 10)
    self.assertTrue(data['total_questions'])
    self.assertTrue(data['categories'].get('1', None))

  def test_get_questions_second_page(self):
    res = self.client().get('/questions?page=2')
    data = json.loads(res.data)

    self.assertEqual(res.status_code, 200)
    self.assertTrue(data['questions'])
    self.assertLessEqual(len(data['questions']), 10)
    self.assertTrue(data['total_questions'])
    self.assertTrue(data['categories'].get('1', None))

  def test_delete_questions(self):
    res = self.client().delete('/questions/' + str(self.question_for_delete_test.id))

    self.assertEqual(res.status_code, 200)
    self.assertFalse(Question.query.get(self.question_for_delete_test.id))

  def test_422_delete_not_existing_question(self):
    res = self.client().delete('/questions/100000')

    self.assertEqual(res.status_code, 422)

  def test_create_question(self):
    new_question = {
      'question': 'test',
      'answer': 'test',
      'difficulty': '1',
      'category': '1'
    }
    
    questions_num_before_create = len(Question.query.all())

    res = self.client().post('/questions', json=new_question)

    questions_num_after_create = len(Question.query.all())

    self.assertEqual(res.status_code, 200)
    self.assertGreater(questions_num_after_create, questions_num_before_create)

  def test_400_create_invalid_question(self):
    new_question = {}
    
    res = self.client().post('/questions', json=new_question)
    self.assertEqual(res.status_code, 400)

  def test_get_specific_category_questions(self):
    res = self.client().get('categories/1/questions')
    data = json.loads(res.data)

    self.assertTrue(res.status_code, 200)
    for question in data['questions']:
      self.assertTrue(question['category'], 1)
    self.assertTrue(data['total_questions'])
    self.assertTrue(data['categories'])
    self.assertEqual(
      data['current_category'],
      Category.query.get(1).type
    )

  def test_404_get_invalid_category_question(self):
    res = self.client().get('categories/100000/questions')
    self.assertTrue(res.status_code, 404)

  def get_next_quizze_in_all_category(self):
    res = self.client().post(
      '/quizzes',
      json={
        'quiz_category': {
          'id': 0
        },
        'previous_questions': [range(2, 100)]
      }
    )
    data = json.loads(res.data)

    self.assertEqual(res.status_code, 200)
    self.assertEqual(data['question']['id'], 1)
 
  def test_get_next_quizze_in_specific_category(self):
    res = self.client().post(
      '/quizzes',
      json={
        'quiz_category': {
          'id': 3
        },
        'previous_questions': []
      }
    )
    data = json.loads(res.data)

    self.assertEqual(res.status_code, 200)
    self.assertEqual(data['question']['category'], 3)

  def test_force_end(self):
    res = self.client().post(
      '/quizzes',
      json={
        'quiz_category': {
          'id': '3'
        },
        'previous_questions': [i for i in range(0,100)]
      }
    )
    data = json.loads(res.data)
    self.assertEqual(res.status_code, 200)
    self.assertFalse(data.get('questions'))

  def test_422_get_invalid_category_quizze(self):
    res = self.client().post(
      '/quizzes',
      json={
        'quize_category': {
          'id': 1000
        },
        'previous_questions': []
      }
    )
    self.assertEqual(res.status_code, 422)
 
# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
