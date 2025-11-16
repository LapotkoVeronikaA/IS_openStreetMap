# app/models.py
from app.extensions import db
import json

# Вспомогательная таблица для связи "многие-ко-многим" между группами и правами
group_permissions = db.Table('group_permissions',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_deletable = db.Column(db.Boolean, nullable=False, default=True) 
    users = db.relationship('User', back_populates='group')
    permissions = db.relationship('Permission', secondary=group_permissions, lazy='subquery',
                                backref=db.backref('groups', lazy=True))
    def __repr__(self):
        return f'<Group {self.name}>'

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) 
    description = db.Column(db.String(255)) 
    def __repr__(self):
        return f'<Permission {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) # Пароль пока храним в открытом виде
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    group = db.relationship('Group', back_populates='users')
    full_name = db.Column(db.String(120))
    position = db.Column(db.String(120))
    activities = db.relationship('UserActivity', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self): return f'<User {self.username}>'

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    legal_name = db.Column(db.String(255))
    org_type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=False) # Фактический адрес для геокодинга
    head_of_organization = db.Column(db.String(150))
    website = db.Column(db.String(200))
    main_phone = db.Column(db.String(100))
    main_email = db.Column(db.String(120))
    departments = db.Column(db.Text, nullable=True) # Замена 'subdivisions'
    contacts = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def set_contacts(self, contacts_list):
        if contacts_list: self.contacts = json.dumps(contacts_list, ensure_ascii=False)
        else: self.contacts = None
    def get_contacts(self):
        if self.contacts:
            try: return json.loads(self.contacts)
            except json.JSONDecodeError: return []
        return []
        
    def set_departments(self, departments_list):
        if departments_list: self.departments = json.dumps(departments_list, ensure_ascii=False)
        else: self.departments = None
    def get_departments(self):
        if self.departments:
            try: return json.loads(self.departments)
            except json.JSONDecodeError: return []
        return []

    @property
    def total_employee_count(self):
        total = 0
        for dept in self.get_departments():
            try:
                total += int(dept.get('employee_count', 0) or 0)
            except (ValueError, TypeError):
                continue
        return total
        
    def __repr__(self): return f'<Organization {self.name}>'

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_activity_user_id'), nullable=True)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    details = db.Column(db.Text) 
    def __repr__(self): return f'<UserActivity {self.username} - {self.action[:30]}>'
    def set_details(self, data): self.details = json.dumps(data, ensure_ascii=False, indent=2)
    def get_details(self):
        if self.details:
            try: return json.loads(self.details)
            except json.JSONDecodeError: return {"error": "Invalid JSON data in details"}
        return None