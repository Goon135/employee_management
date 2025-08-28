from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from models import db, Employee
from config import Config
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Инициализация базы данных
    db.init_app(app)
    
    @app.route('/')
    def index():
        return redirect(url_for('employees_list'))
    
    @app.route('/employees')
    def employees_list():
        try:
            # Получение параметров запроса
            search_query = request.args.get('search', '').strip()
            sort_field = request.args.get('sort', 'id')
            sort_order = request.args.get('order', 'asc')
            
            # Базовый запрос
            query = Employee.query
            
            # Поиск по ФИО
            if search_query:
                query = query.filter(
                    or_(
                        Employee.full_name.ilike(f'%{search_query}%'),
                        Employee.full_name.ilike(f'{search_query}%')
                    )
                )
            
            # Сортировка
            if hasattr(Employee, sort_field):
                field = getattr(Employee, sort_field)
                if sort_order == 'desc':
                    field = field.desc()
                query = query.order_by(field)
            
            # Получение сотрудников
            employees = query.all()
            
            return render_template('employees.html', 
                                 employees=employees,
                                 search_query=search_query,
                                 sort_field=sort_field,
                                 sort_order=sort_order)
            
        except SQLAlchemyError as e:
            flash(f'Ошибка базы данных: {str(e)}', 'error')
            return render_template('employees.html', employees=[])
    
    @app.route('/api/employees/<int:employee_id>/manager', methods=['PUT'])
    def update_manager(employee_id):
        try:
            data = request.get_json()
            new_manager_id = data.get('manager_id')
            
            # Проверка существования сотрудника
            employee = Employee.query.get_or_404(employee_id)
            
            # Проверка циклических ссылок
            if new_manager_id:
                # Нельзя назначить себя своим начальником
                if employee_id == new_manager_id:
                    return jsonify({'error': 'Сотрудник не может быть своим начальником'}), 400
                
                # Проверка существования нового начальника
                new_manager = Employee.query.get(new_manager_id)
                if not new_manager:
                    return jsonify({'error': 'Начальник не найден'}), 404
                
                # Проверка на циклическую иерархию
                current = new_manager
                while current.manager_id:
                    if current.manager_id == employee_id:
                        return jsonify({'error': 'Обнаружена циклическая ссылка в иерархии'}), 400
                    current = Employee.query.get(current.manager_id)
            
            # Обновление начальника
            employee.manager_id = new_manager_id
            db.session.commit()
            
            return jsonify({
                'message': 'Начальник успешно обновлен',
                'employee': employee.to_dict()
            })
            
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'Ошибка целостности данных'}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': f'Ошибка базы данных: {str(e)}'}), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Ресурс не найден'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)