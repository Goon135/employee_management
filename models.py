from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Связь с самим собой (начальник-подчиненный)
    manager = db.relationship('Employee', 
                             remote_side=[id],
                             backref=db.backref('subordinates', lazy='dynamic'),
                             foreign_keys=[manager_id])
    
    def __repr__(self):
        return f'<Employee {self.full_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'position': self.position,
            'hire_date': self.hire_date.isoformat(),
            'salary': self.salary,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None
        }