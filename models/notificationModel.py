# models/notificationModel.py

from datetime import datetime, timezone
from app import db

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # relationship para UserNotification, cascade na ORM
    users = db.relationship(
        'UserNotification',
        back_populates='notification',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<Notification {self.id}>'

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id', ondelete='CASCADE'), nullable=False)
    viewed = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('user_notifications', lazy='dynamic', cascade='all, delete-orphan'))
    notification = db.relationship('Notification', back_populates='users')

    def __repr__(self):
        return f'<UserNotification user={self.user_id} notification={self.notification_id}>'
