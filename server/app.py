#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        # Validate that username is provided
        if not data.get('username'):
            return {'errors': ['Username is required']}, 422
        
        try:
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data.get('password')
            
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 201
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username already exists']}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'errors': ['Not authorized']}, 401
        
        user = User.query.get(user_id)
        if not user:
            return {'errors': ['Not authorized']}, 401
        
        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }, 200

class Login(Resource):
    def post(self):
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.authenticate(password):
            return {'errors': ['Invalid username or password']}, 401
        
        session['user_id'] = user.id
        
        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }, 200

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'errors': ['Not authorized']}, 401
        
        session.clear()
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'errors': ['Not authorized']}, 401
        
        user = User.query.get(user_id)
        if not user:
            return {'errors': ['Not authorized']}, 401
        
        recipes = [
            {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user_id': recipe.user_id
            }
            for recipe in user.recipes
        ]
        
        return recipes, 200
    
    def post(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'errors': ['Not authorized']}, 401
        
        data = request.get_json()
        
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            return {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user_id': recipe.user_id
            }, 201
        except IntegrityError as e:
            db.session.rollback()
            return {'errors': ['Invalid recipe data']}, 422
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)