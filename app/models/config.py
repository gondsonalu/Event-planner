from app import db

class SystemConfiguration(db.Model):
    __tablename__ = 'system_configuration'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)

    @staticmethod
    def get_setting(key, default=None):
        setting = SystemConfiguration.query.filter_by(key=key).first()
        if setting:
            if setting.value == 'True': return True
            if setting.value == 'False': return False
            return setting.value
        return default

    @staticmethod
    def set_setting(key, value, description=None):
        setting = SystemConfiguration.query.filter_by(key=key).first()
        if not setting:
            setting = SystemConfiguration(key=key, value=str(value), description=description)
            db.session.add(setting)
        else:
            setting.value = str(value)
            if description:
                setting.description = description
        db.session.commit()
