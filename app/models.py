# app/models.py
from app.extensions import db
import json
from sqlalchemy import UniqueConstraint

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
    password = db.Column(db.String(120), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    group = db.relationship('Group', back_populates='users')
    full_name = db.Column(db.String(120))
    department = db.Column(db.String(120))
    position = db.Column(db.String(120))
    contact_info = db.Column(db.Text)
    activities = db.relationship('UserActivity', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<User {self.username}>'

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

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    
    # Иерархия: родитель и дети
    parent_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    children = db.relationship('Organization', backref=db.backref('parent', remote_side=[id]), lazy='dynamic', cascade="all, delete-orphan")

    name = db.Column(db.String(255), nullable=False, index=True)
    legal_name = db.Column(db.String(255))
    org_type = db.Column(db.String(100), nullable=True) 
    
    location = db.Column(db.String(255), nullable=True)
    
    head_of_organization = db.Column(db.String(150))
    head_position = db.Column(db.String(150))
    
    website = db.Column(db.String(200))
    main_phone = db.Column(db.String(100))
    main_email = db.Column(db.String(120))
    
    contacts = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text)
    
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    events = db.relationship('Event', back_populates='organization', lazy='dynamic', cascade="all, delete-orphan")
    
    def set_contacts(self, contacts_list):
        if contacts_list: self.contacts = json.dumps(contacts_list, ensure_ascii=False)
        else: self.contacts = None
    def get_contacts(self):
        if self.contacts:
            try: return json.loads(self.contacts)
            except json.JSONDecodeError: return []
        return []
        
    @property
    def total_employee_count(self):
        return len(self.get_contacts())

    @property
    def website_url(self):
        """Возвращает абсолютную ссылку на сайт (с http), даже если введено просто www..."""
        if not self.website:
            return None
        if self.website.startswith('http://') or self.website.startswith('https://'):
            return self.website
        return f'http://{self.website}'
        
    def __repr__(self): return f'<Organization {self.name}>'

class GenericDirectoryItem(db.Model):
    __tablename__ = 'generic_directory_item'
    
    id = db.Column(db.Integer, primary_key=True)
    directory_type = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    __table_args__ = (UniqueConstraint('directory_type', 'name', name='uq_directory_type_name'),)

    def __repr__(self):
        return f'<GenericDirectoryItem [{self.directory_type}] {self.name}>'

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<Feedback {self.subject}>'

class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    user = db.relationship('User')

    def __repr__(self):
        return f'<News {self.title}>'

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    organization = db.relationship('Organization', back_populates='events')

    def __repr__(self):
        return f'<Event {self.title}>'