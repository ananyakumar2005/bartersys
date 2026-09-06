from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


# ---------------------------------------------------------------------------
# Auth forms
# ---------------------------------------------------------------------------

class SignupForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


# ---------------------------------------------------------------------------
# Item / Listing forms
# ---------------------------------------------------------------------------

CATEGORY_CHOICES = [
    ("", "Select a category"),
    ("books", "Books & Study Material"),
    ("electronics", "Electronics"),
    ("clothing", "Clothing & Accessories"),
    ("sports", "Sports & Fitness"),
    ("stationery", "Stationery"),
    ("food", "Food & Kitchen"),
    ("other", "Other"),
]

CONDITION_CHOICES = [
    ("", "Select condition"),
    ("new", "New / Unused"),
    ("good", "Good"),
    ("fair", "Fair"),
    ("poor", "Heavily Used"),
]


class ItemForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    category = SelectField("Category", choices=CATEGORY_CHOICES, validators=[Optional()])
    condition = SelectField("Condition", choices=CONDITION_CHOICES, validators=[Optional()])
    images = FileField("Photos", validators=[Optional()])  # multi-file handled in template


# ---------------------------------------------------------------------------
# Barter Request form
# ---------------------------------------------------------------------------

class BarterRequestForm(FlaskForm):
    offered_item_id = SelectField("Offer in exchange", coerce=int, validators=[Optional()])
    message = TextAreaField("Message to owner", validators=[Optional(), Length(max=500)])


# ---------------------------------------------------------------------------
# Wanted board form
# ---------------------------------------------------------------------------

class ItemRequestForm(FlaskForm):
    title = StringField("What are you looking for?", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Details", validators=[Optional(), Length(max=1000)])
    category = SelectField("Category", choices=CATEGORY_CHOICES, validators=[Optional()])
