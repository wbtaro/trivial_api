import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging
from logging import Formatter, FileHandler
import random
import sys

from models import setup_db, db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  cors = CORS(app, resources={r'/*': {'origins': '*'}})

  # load test_config
  if test_config:
    app.debug = test_config['debug']

  # set logger
  logger = logging.getLogger(__name__)
  if app.debug:
    handler = logging.StreamHandler(sys.stdout)
  else:
    handler = FileHandler('error.log')
  handler.setFormatter(
    Formatter(
      '%(asctime)s %(levelname)s: \
      %(message)s [in %(pathname)s:%(lineno)d]'
    )
  )

  handler.setLevel(logging.WARNING)
  logger.addHandler(handler)

  @app.after_request
  def after_request(response):
    response.headers.add(
      'Access-Control-Allow-Headers',
      'Content-Type,Authorization,true'
    )
    response.headers.add(
      'Access-Control-Allow-Methods',
      '*'
    )
    return response

  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    ret_categories = {}
    for category in categories:
      ret_categories[category.id] = category.type

    return jsonify({
      'success': True,
      'total_categories': len(categories),
       'categories': ret_categories
    })

  def pagenate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    currenst_questions = questions[start:end]

    return currenst_questions

  @app.route('/questions')
  def get_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = pagenate_questions(request, selection)

    categories = Category.query.all()
    ret_categories = {}
    for category in categories:
      ret_categories[category.id] = category.type

    return jsonify({
        'questions': current_questions,
        'total_questions': len(selection),
        'categories': ret_categories,
    })

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      Question.query.get(question_id).delete()
      return jsonify({
        'success': True
      })
    except Exception as e:
      logger.warning(e)
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    question = Question(
      question=body.get('question', None),
      answer=body.get('answer', None),
      category=body.get('category', None),
      difficulty=body.get('difficulty', None)
    )

    if (not question.question) |\
      (not question.answer) |\
      (not question.category) |\
      (not question.difficulty):
      abort(400)

    try:
      question.insert()
      return jsonify({
        'success': True
      })
    except Exception as e:
      logger.warning(e)
      abort(422)

  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    try:
      search_term = "%{}%".format(request.get_json().get('searchTerm', ''))
        
      result = []
      if search_term:
        result = Question.query.filter(Question.question.like(search_term)).all()
      else:
        result = Question.query.all()

      return jsonify({
        'questions': [question.format() for question in result],
        'total_questions': len(result)
      })
    except Exception as e:
      logger.warning(e)
      abort(422)

  @app.route('/categories/<int:category_id>/questions')
  def get_carrent_category_questions(category_id):
    try:
      selection = Question.query.filter_by(category=category_id).order_by(Question.id).all()
      current_questions = pagenate_questions(request, selection)

      categories = Category.query.all()
      ret_categories = {}
      for category in categories:
        ret_categories[category.id] = category.type

      return jsonify({
        'questions': current_questions,
        'total_questions': len(selection),
        'categories': ret_categories,
        'current_category': Category.query.get(category_id).type,
      })
    except Exception as e:
      logger.warning(e)
      abort(404)

  @app.route('/quizzes', methods=['POST'])
  def get_next_quizze():
    body = request.get_json()
    try:
      quiz_category = body.get('quiz_category', None).get('id', None)
      previous_questions = body.get('previous_questions', [])
      questions = []
      if quiz_category != 0:
        questions = Question.query.filter_by(category=quiz_category).all()
      else:
        questions = Question.query.all()

      next_question = None
      force_end = True
      for _ in range(len(questions)):
        next_question = random.sample(questions, 1).pop()
        if next_question.id not in previous_questions:
          force_end = False
          break

      if force_end:
        return jsonify({
          'message': 'no questions to return'
        })
      else:
        return jsonify({
          'question': next_question.format()
        })
    except Exception as e:
      logger.warning(e)
      abort(422)

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
    }), 400

  @app.errorhandler(401)
  def unauthorized(error):
    return jsonify({
      "success": False, 
      "error": 401,
      "message": "unauthorized"
    }), 401

  @app.errorhandler(403)
  def access_frobidden(error):
    return jsonify({
      "success": False, 
      "error": 403,
      "message": "access forbidden"
    }), 403

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
    }), 404

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      "success": False, 
      "error": 405,
      "message": "method not allowed"
    }), 405

  @app.errorhandler(409)
  def conflict(error):
    return jsonify({
      "success": False, 
      "error": 409,
      "message": "conflict"
    }), 409

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
    }), 422

  @app.errorhandler(500)
  def server_error(error):
    return jsonify({
      "success": False, 
      "error": 500,
      "message": "server error"
    }), 500
    
  return app
