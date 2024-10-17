"""The models of the api tables"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Index, Enum, ForeignKey, DateTime
from flask_sqlalchemy import SQLAlchemy
import enum
from const import TxtData

db = SQLAlchemy()


class BaseModel(db.Model):
    """Abstract class for using in other models creation"""


    __abstract__ = True

    def to_dict(self):

        """The method for queries results unpacking"""

        try:
            created_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
            return created_dict
        except:
            raise ValueError(TxtData.DictConvertError)


class Levels(enum.Enum):
    A1 = 'A1'
    A2 = 'A2'
    B1 = 'B1'
    B2 = 'B2'
    C1 = 'C1'


class Questions(BaseModel):

    """the main table with questions list. 
    datetime_shown is for reflecting the time when a question was shown to a user last time"""

    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index= True, autoincrement=True)
    level: Mapped[Enum] = mapped_column(Enum(Levels), nullable=False)
    question: Mapped[Text] = mapped_column(String(400), nullable=False)
    correct_id: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[Text] = mapped_column(String(500))
    #correct_id: Mapped[int] = mapped_column(Integer, ForeignKey('options.option_id'), nullable=False)
    datetime_shown: Mapped[DateTime] = mapped_column(DateTime, default=None, nullable=True)

    def to_dict(self):
        d = super().to_dict()
        d["level"] = self.level.value  #because otherwise enum will not be JSON serializable
        return d


class Options(BaseModel):

    """the table with possible answers"""

    __tablename__ = 'options'

    #question_id: Mapped[int] = mapped_column(Integer,  primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer,  ForeignKey('questions.id'), primary_key=True)
    option_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    option_text: Mapped[Text] = mapped_column(String(200), nullable=False)

    __table_args__ = (
        Index('ix_question_option', 'question_id', 'option_id', unique=True),
    )



