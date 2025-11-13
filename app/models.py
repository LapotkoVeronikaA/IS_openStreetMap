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
    org_type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    head_of_organization = db.Column(db.String(150))
    notes = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
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