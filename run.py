import os
import datetime
import json
from io import BytesIO
import re
import traceback
from flask import (Flask, render_template, request, jsonify, abort,
                   session, redirect, url_for, flash, send_file, Blueprint)
from flask_sqlalchemy import SQLAlchemy
import openpyxl
from openpyxl import Workbook
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

views = Blueprint('views', __name__)
app = Flask(__name__)

# --- App Configuration ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_insecure_default_secret_key_CHANGE_ME_NOW')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///invoices.db')  # Use file-based SQLite for persistence
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE1_URL', 'postgresql://neondb_owner:npg_zG0sAqhX8OFP@ep-raspy-glitter-a4eqnhhs-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Define Excel Log Headers ---
EXCEL_LOG_HEADERS = [
    "LogTimestamp", "InvoiceNumber", "DocumentType", "PrintDate", "Reference",
    "Purpose", "Category", "BillingMonthYear", "GSTIN", "Billedto",
    "PaymentMethod", "ReverseCharge", "AdvancePayment", "SubTotal",
    "DiscountApplied", "DiscountPercentage", "DiscountAmount", "GrandTotal",
    "LineItems_Count", "LineItems_CostCategories", "LineItems_Descriptions",
    "LineItems_SACs", "LineItems_RatesAndUnits", "LineItems_ConsumedUnitsAndUnits", "LineItems_Totals"
]

# --- Database Models ---
class ReferenceOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    __tablename__ = 'reference_option'

class PurposeOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    __tablename__ = 'purpose_option'

class CategoryOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    __tablename__ = 'category_option'

class GstinOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(15), unique=True, nullable=False)
    __tablename__ = 'gstin_option'

class GstoutOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(15), unique=True, nullable=False)
    __tablename__ = 'gstout_option'

class DescriptionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    __tablename__ = 'description_option'

class SacOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    __tablename__ = 'sac_option'

class ReverseChargeOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(5), unique=True, nullable=False)
    __tablename__ = 'reverse_charge_option'

class PaymentMethodOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    __tablename__ = 'payment_method_option'

class CostCategoryOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    __tablename__ = 'cost_category_option'

class InvoiceSequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    fixed_prefix = db.Column(db.String(100), nullable=False)
    fixed_code = db.Column(db.String(50), nullable=False)
    financial_year = db.Column(db.String(10), nullable=False)
    last_number = db.Column(db.Integer, default=0, nullable=False)
    __tablename__ = 'invoice_sequence'

class InvoiceLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_timestamp = db.Column(db.String(20))
    invoice_number = db.Column(db.String(100))
    document_type = db.Column(db.String(50))
    print_date = db.Column(db.String(10))
    reference = db.Column(db.String(100))
    purpose = db.Column(db.String(100))
    category = db.Column(db.String(100))
    billing_month_year = db.Column(db.String(20))
    gstin = db.Column(db.String(15))
    billed_to = db.Column(db.String(200))
    payment_method = db.Column(db.String(100))
    reverse_charge = db.Column(db.String(5))
    advance_payment = db.Column(db.String(5))
    sub_total = db.Column(db.Float)
    discount_applied = db.Column(db.String(5))
    discount_percentage = db.Column(db.Float)
    discount_amount = db.Column(db.Float)
    grand_total = db.Column(db.Float)
    line_items_count = db.Column(db.Integer)
    line_items_cost_categories = db.Column(db.Text)
    line_items_descriptions = db.Column(db.Text)
    line_items_sacs = db.Column(db.Text)
    line_items_rates_and_units = db.Column(db.Text)
    line_items_consumed_units_and_units = db.Column(db.Text)
    line_items_totals = db.Column(db.Text)
    user_id = db.Column(db.String(50))
    __tablename__ = 'invoice_log'

# --- Model Mapping ---
MODEL_MAP = {
    'reference': {'model': ReferenceOption, 'field': 'name'},
    'purpose': {'model': PurposeOption, 'field': 'name'},
    'category': {'model': CategoryOption, 'field': 'name'},
    'gstin': {'model': GstinOption, 'field': 'value'},
    'gstout': {'model': GstoutOption, 'field': 'value'},
    'itemDescription': {'model': DescriptionOption, 'field': 'name'},
    'itemSac': {'model': SacOption, 'field': 'code'},
    'reverseCharge': {'model': ReverseChargeOption, 'field': 'value'},
    'paymentMethod': {'model': PaymentMethodOption, 'field': 'name'},
    'costCategory': {'model': CostCategoryOption, 'field': 'name'},
}

# --- Flask-Login Configuration ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "info"

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

users_db = {
    "1": User(id="1", username="admin", password_hash=generate_password_hash("password123")),
    "2": User(id="2", username="user", password_hash=generate_password_hash("test")),
    "3": User(id="3", username="Abhi", password_hash=generate_password_hash("test123")),
}

@login_manager.user_loader
def load_user(user_id):
    return users_db.get(user_id)

# --- Helper Functions ---
def get_indian_financial_year(date=None):
    if date is None:
        date = datetime.date.today()
    year = date.year
    month = date.month
    if month < 4:
        financial_year_start = year - 1
        financial_year_end = year
    else:
        financial_year_start = year
        financial_year_end = year + 1
    return f"{financial_year_start}-{str(financial_year_end)[-2:]}"

def add_initial_data():
    initial_data = {
        ReferenceOption: ["Ref001", "Ref002", "Project X", "Support Ticket"],
        PurposeOption: ["Consulting Services", "Software Development", "Annual Maintenance", "Training"],
        CategoryOption: ["Software License", "Hardware Sale", "Professional Services", "Subscription"],
        GstoutOption: ["30KLMNO9876P1Z0", "31QRSTU5432V1ZA", "Not Applicable"],
        GstinOption: ["29ABCDE1234F1Z5", "27FGHIJ5678K1Z9", "N/A", "URP"],
        DescriptionOption: ["Web Development Hours", "API Integration Setup", "Server Maintenance (Monthly)", "Consulting Call"],
        SacOption: ["998314", "998315", "998319", "998311"],
        ReverseChargeOption: ["Yes", "No"],
        PaymentMethodOption: ["Bank Transfer (NEFT/RTGS)", "Credit Card", "UPI", "Cheque"],
        CostCategoryOption: ["Travel", "Accommodation", "Software", "Hardware", "Services", "Miscellaneous"]
    }
    with app.app_context():
        db.create_all()
        needs_commit = False
        for model, items in initial_data.items():
            try:
                if model.query.count() == 0:
                    print(f"Populating initial data for {model.__tablename__}...")
                    needs_commit = True
                    field_name = None
                    if hasattr(model, 'name'):
                        field_name = 'name'
                    elif hasattr(model, 'value'):
                        field_name = 'value'
                    elif hasattr(model, 'code'):
                        field_name = 'code'
                    if field_name:
                        for item in items:
                            record = model(**{field_name: item})
                            db.session.add(record)
                    else:
                        print(f"Warning: Could not determine field name for model {model.__name__}")
            except Exception as e:
                print(f"Error querying or populating {model.__name__}: {e}")
        if needs_commit:
            try:
                db.session.commit()
                print("Initial data committed.")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing initial data: {e}")
        else:
            print("Initial data already exists or no data to add.")

def add_new_option_if_needed(option_type, selected_value, new_value_str):
    if selected_value != 'Add New':
        return False, selected_value
    new_value = (new_value_str or '').strip()
    if not new_value:
        return False, 'Add New'
    if option_type not in MODEL_MAP:
        print(f"Warning: Unknown option type '{option_type}' for adding.")
        return False, new_value
    mapping = MODEL_MAP[option_type]
    model = mapping['model']
    field = mapping['field']
    try:
        exists = model.query.filter(getattr(model, field) == new_value).first()
        if not exists:
            new_record = model(**{field: new_value})
            db.session.add(new_record)
            return True, new_value
        else:
            return False, getattr(exists, field)
    except Exception as e:
        print(f"Error processing new {option_type} '{new_value}': {e}")
        return False, new_value

def flatten_line_items(line_items):
    if not line_items:
        return 0, "", "", "", "", "", ""
    count = len(line_items)
    cost_categories = "; ".join([str(item.get('costCategory', '')) for item in line_items])
    descriptions = "; ".join([str(item.get('description', '')) for item in line_items])
    sacs = "; ".join([str(item.get('sac', '')) for item in line_items])
    rates = "; ".join([f"{item.get('rateValue', '')} per {item.get('rateUnit', '')}" for item in line_items])
    units = "; ".join([f"{item.get('unitsConsumedValue', '')} {item.get('unitsConsumedUnit', '')}" for item in line_items])
    totals = "; ".join([str(item.get('total', '')) for item in line_items])
    return count, cost_categories, descriptions, sacs, rates, units, totals

def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user_found = None
        for user in users_db.values():
            if user.username.lower() == username.lower():
                user_found = user
                break
        if user_found and user_found.check_password(password):
            login_user(user_found, remember=remember)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    db_data = {}
    try:
        for key, mapping in MODEL_MAP.items():
            model = mapping['model']
            field = mapping['field']
            options = model.query.order_by(db.func.lower(getattr(model, field))).all()
            db_data[key + '_options'] = options
    except Exception as e:
        print(f"Error loading options from database: {e}")
        traceback.print_exc()
        for key in MODEL_MAP.keys():
            db_data[key + '_options'] = []
    preview_data = session.get('preview_data', None)
    return render_template('index3.html', data=db_data, preview_data_json=json.dumps(preview_data))

@app.route('/generate', methods=['POST'])
@login_required
def generate_document():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    form_data = request.get_json()
    processed_form_data = {}
    db_commit_needed = False
    fields_to_check = [
        'reference', 'purpose', 'category', 'gstin', 'gstout',
        'reverseCharge', 'paymentMethod', 'costCategory'
    ]
    for field_key in fields_to_check:
        selected_key = f'{field_key}Selected'
        new_value_key = f'new{field_key.capitalize()}'
        selected_value = form_data.get(selected_key)
        new_value_str = form_data.get(new_value_key, '')
        if selected_key in form_data:
            added, final_value = add_new_option_if_needed(field_key, selected_value, new_value_str)
            db_commit_needed = db_commit_needed or added
            processed_form_data[field_key] = final_value
    processed_form_data['docType'] = form_data.get('docType')
    processed_form_data['monthYear'] = form_data.get('monthYear')
    processed_form_data['applyDiscount'] = form_data.get('applyDiscount')
    processed_form_data['discountPercentage'] = form_data.get('discountPercentage')
    processed_form_data['advancePayment'] = form_data.get('advancePayment')
    processed_form_data['subTotal'] = form_data.get('subTotal')
    processed_form_data['discountAmount'] = form_data.get('discountAmount')
    processed_form_data['grandTotal'] = form_data.get('grandTotal')
    processed_form_data['billedTo'] = form_data.get('billedTo')
    processed_line_items = []
    if 'lineItems' in form_data:
        line_item_fields_to_add_option = {
            'costCategory': 'costCategory',
            'description': 'itemDescription',
            'sac': 'itemSac',
        }
        for item in form_data['lineItems']:
            processed_item = item.copy()
            for item_field_key, option_type in line_item_fields_to_add_option.items():
                item_value = item.get(item_field_key, '')
                if item_value and option_type in MODEL_MAP:
                    added, final_item_value = add_new_option_if_needed(option_type, 'Add New', item_value)
                    db_commit_needed = db_commit_needed or added
                    processed_item[item_field_key] = final_item_value
            processed_line_items.append(processed_item)
    processed_form_data['lineItems'] = processed_line_items
    if db_commit_needed:
        try:
            db.session.commit()
            print("New options committed.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing new options: {e}")
            flash(f'Error saving new options: {e}', 'danger')
    if 'invoiceNumber' in processed_form_data:
        del processed_form_data['invoiceNumber']
    if 'currentDate' in processed_form_data:
        del processed_form_data['currentDate']
    session['preview_data'] = processed_form_data
    return jsonify({"redirect": url_for('preview_page')})

@app.route('/preview')
@login_required
def preview_page():
    preview_data = session.get('preview_data')
    if not preview_data:
        flash('No preview data found or session expired. Please generate the document again.', 'warning')
        return redirect(url_for('index'))
    return render_template('test2_updated.html', preview_data=preview_data)

@app.route('/edit')
@login_required
def edit_from_preview():
    session.pop('preview_data', None)
    flash('Returning to form. Please make your changes and regenerate.', 'info')
    return redirect(url_for('index'))

@app.route('/delete_preview', methods=['POST'])
@login_required
def delete_preview():
    session.pop('preview_data', None)
    flash('Document data cleared. Please fill the form again.', 'info')
    return jsonify({"redirect": url_for('index')})

@app.route('/clear_preview_data', methods=['POST'])
@login_required
def clear_preview_data():
    session.pop('preview_data', None)
    print("Preview data cleared from session.")
    return jsonify({"success": True, "message": "Preview data cleared."})

@app.route('/get_invoice_sequence_info', methods=['GET'])
@login_required
def get_invoice_sequence_info():
    user_id = current_user.id
    current_financial_year = get_indian_financial_year()
    try:
        sequence = InvoiceSequence.query.filter_by(user_id=user_id).first()
        if not sequence:
            print(f"Sequence setup needed for user {user_id}")
            return jsonify({"status": "needs_setup", "financialYear": current_financial_year})
        if sequence.financial_year != current_financial_year:
            print(f"Financial year changed for user {user_id}. Resetting sequence.")
            sequence.last_number = 0
            sequence.financial_year = current_financial_year
            db.session.commit()
        prefix_part = sequence.fixed_prefix.strip()
        code_part = sequence.fixed_code.strip()
        year_part = sequence.financial_year
        next_num_pred = sequence.last_number + 1
        format_example = f"{prefix_part}/{year_part}/{code_part}/{next_num_pred}"
        return jsonify({
            "status": "info",
            "fixedPrefix": prefix_part,
            "fixedCode": code_part,
            "financialYear": year_part,
            "lastNumber": sequence.last_number,
            "nextNumberPrediction": next_num_pred,
            "formatExample": format_example
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error getting invoice sequence info for user {user_id}: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Server error getting sequence info: {str(e)}"}), 500

@app.route('/setup_invoice_sequence', methods=['POST'])
@login_required
def setup_invoice_sequence():
    user_id = current_user.id
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400
    fixed_prefix = data.get('fixedPrefix')
    fixed_code = data.get('fixedCode')
    starting_number = data.get('startingNumber')
    if fixed_prefix is None or fixed_code is None or starting_number is None:
        return jsonify({"success": False, "message": "Fixed prefix, fixed code, and starting number are required."}), 400
    try:
        starting_number = int(starting_number)
        if starting_number < 0:
            raise ValueError("Negative number not allowed.")
    except ValueError:
        return jsonify({"success": False, "message": "Starting number must be a non-negative integer."}), 400
    existing_sequence = InvoiceSequence.query.filter_by(user_id=user_id).first()
    if existing_sequence:
        print(f"Setup attempted but sequence already exists for user {user_id}")
        return jsonify({"success": False, "message": "Invoice sequence already exists for this user."}), 409
    current_financial_year = get_indian_financial_year()
    new_sequence = InvoiceSequence(
        user_id=user_id,
        fixed_prefix=fixed_prefix.strip(),
        fixed_code=fixed_code.strip(),
        financial_year=current_financial_year,
        last_number=starting_number - 1
    )
    try:
        db.session.add(new_sequence)
        db.session.commit()
        print(f"Invoice sequence setup successfully for user {user_id}.")
        return jsonify({"success": True, "message": "Invoice sequence set up successfully."})
    except Exception as e:
        db.session.rollback()
        print(f"Error setting up invoice sequence for user {user_id}: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error setting up sequence: {str(e)}"}), 500

@app.route('/log_document_to_excel', methods=['POST'])
@login_required
def log_document_to_excel():
    data = request.get_json()
    if not data:
        print(f"User {current_user.id}: No data received in log_document_to_excel")
        return jsonify({"success": False, "message": "No data received."}), 400
    user_id = current_user.id
    current_financial_year = get_indian_financial_year()
    invoice_number_to_log = 'ASSIGNMENT_FAILED'
    log_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manual_date = data.get('manualDate')
    print_date = manual_date if (manual_date and validate_date(manual_date)) else datetime.datetime.now().strftime("%Y-%m-%d")
    manual_number_part_str = data.get('manualInvoiceNumberPart')
    manual_number_part = None
    used_manual_number = False
    if manual_number_part_str:
        try:
            manual_number_part = int(manual_number_part_str)
            if manual_number_part <= 0:
                raise ValueError("Manual number must be positive.")
            print(f"User {user_id} provided manual number part: {manual_number_part}")
        except (ValueError, TypeError) as e:
            print(f"User {user_id}: Invalid manual number part '{manual_number_part_str}' - {e}")
            manual_number_part = None
    try:
        sequence = InvoiceSequence.query.filter_by(user_id=user_id).with_for_update().first()
        if not sequence:
            print(f"User {user_id}: Log attempt failed - Sequence setup needed")
            db.session.rollback()
            return jsonify({"status": "needs_setup"})
        if sequence.financial_year != current_financial_year:
            print(f"User {user_id}: Financial year changed. Resetting sequence.")
            sequence.last_number = 0
            sequence.financial_year = current_financial_year
            db.session.commit()
            sequence = InvoiceSequence.query.filter_by(user_id=user_id).with_for_update().first()
        assigned_number_part = sequence.last_number + 1
        if manual_number_part is not None:
            assigned_number_part = manual_number_part
            used_manual_number = True
            sequence.last_number = max(manual_number_part, sequence.last_number + 1)
            print(f"User {user_id}: Used manual number {manual_number_part}. Sequence last_number updated to {sequence.last_number}.")
        else:
            sequence.last_number = assigned_number_part
            print(f"User {user_id}: Assigned sequential number {assigned_number_part}. Sequence last_number updated to {sequence.last_number}.")
        db.session.commit()
        prefix_part = sequence.fixed_prefix.strip()
        code_part = sequence.fixed_code.strip()
        year_part = sequence.financial_year
        invoice_number_to_log = f"{prefix_part}/{year_part}/{code_part}/{assigned_number_part:04d}"
        print(f"User {user_id}: Final number for logging: {invoice_number_to_log}")
        line_items = data.get('lineItems', [])
        (item_count, item_cats, item_descs, item_sacs,
         item_rates, item_units, item_totals) = flatten_line_items(line_items)
        log_entry = InvoiceLog(
            log_timestamp=log_timestamp,
            invoice_number=invoice_number_to_log,
            document_type=data.get('docType', 'N/A').upper(),
            print_date=print_date,
            reference=data.get('reference', 'N/A'),
            purpose=data.get('purpose', 'N/A'),
            category=data.get('category', 'N/A'),
            billing_month_year=data.get('monthYear', 'N/A'),
            gstin=data.get('gstin', 'N/A'),
            billed_to=data.get('billedTo', 'N/A'),
            payment_method=data.get('paymentMethod', 'N/A'),
            reverse_charge=data.get('reverseCharge', 'N/A'),
            advance_payment='Yes' if data.get('advancePayment') else 'No',
            sub_total=data.get('subTotal', 0.0),
            discount_applied='Yes' if data.get('applyDiscount') else 'No',
            discount_percentage=data.get('discountPercentage', 0.0) if data.get('applyDiscount') else 0.0,
            discount_amount=data.get('discountAmount', 0.0) if data.get('applyDiscount') else 0.0,
            grand_total=data.get('grandTotal', 0.0),
            line_items_count=item_count,
            line_items_cost_categories=item_cats,
            line_items_descriptions=item_descs,
            line_items_sacs=item_sacs,
            line_items_rates_and_units=item_rates,
            line_items_consumed_units_and_units=item_units,
            line_items_totals=item_totals,
            user_id=user_id
        )
        db.session.add(log_entry)
        db.session.commit()
        print(f"User {user_id}: Successfully logged invoice {invoice_number_to_log} to database.")
        # Verify the log entry was saved
        saved_log = InvoiceLog.query.filter_by(user_id=user_id, invoice_number=invoice_number_to_log).first()
        if not saved_log:
            print(f"User {user_id}: CRITICAL - Invoice {invoice_number_to_log} was not saved to database!")
            return jsonify({"success": False, "message": "Failed to save invoice to database."}), 500
        if 'preview_data' in session and isinstance(session['preview_data'], dict):
            session['preview_data']['invoiceNumber'] = invoice_number_to_log
            session['preview_data']['currentDate'] = print_date
            session.modified = True
        return jsonify({
            "success": True,
            "invoiceNumber": invoice_number_to_log,
            "currentDate": print_date,
            "usedManualNumber": used_manual_number
        })
    except Exception as e:
        db.session.rollback()
        print(f"User {user_id}: CRITICAL Error during log/assignment for invoice {invoice_number_to_log}: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error logging data or assigning number: {str(e)}"}), 500

@app.route('/download_invoice_log', methods=['GET'])
@login_required
def download_invoice_log():
    try:
        logs = InvoiceLog.query.filter_by(user_id=current_user.id).order_by(InvoiceLog.log_timestamp).all()
        print(f"User {current_user.id}: Found {len(logs)} invoice logs for download.")
        if not logs:
            flash("No invoice logs found for your account.", "info")
            return jsonify({"success": False, "message": "No invoice logs found."}), 404
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(EXCEL_LOG_HEADERS)
        for log in logs:
            worksheet.append([
                log.log_timestamp,
                log.invoice_number,
                log.document_type,
                log.print_date,
                log.reference,
                log.purpose,
                log.category,
                log.billing_month_year,
                log.gstin,
                log.billed_to,
                log.payment_method,
                log.reverse_charge,
                log.advance_payment,
                log.sub_total,
                log.discount_applied,
                log.discount_percentage,
                log.discount_amount,
                log.grand_total,
                log.line_items_count,
                log.line_items_cost_categories,
                log.line_items_descriptions,
                log.line_items_sacs,
                log.line_items_rates_and_units,
                log.line_items_consumed_units_and_units,
                log.line_items_totals
            ])
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        print(f"User {current_user.id}: Excel file generated successfully.")
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'invoice_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        print(f"User {current_user.id}: Error generating Excel download: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error generating Excel file: {str(e)}"}), 500

@app.route('/view_logs')
@login_required
def view_logs():
    try:
        logs = InvoiceLog.query.filter_by(user_id=current_user.id).order_by(InvoiceLog.log_timestamp.desc()).all()
        print(f"User {current_user.id}: Retrieved {len(logs)} logs for viewing.")
        return render_template('view_logs.html', logs=logs)
    except Exception as e:
        print(f"User {current_user.id}: Error retrieving logs: {e}")
        flash("Error retrieving invoice logs.", "danger")
        return redirect(url_for('index'))

@app.route('/get_options/<option_type>', methods=['GET'])
@login_required
def get_options(option_type):
    if option_type not in MODEL_MAP:
        abort(404, description="Option type not found.")
    mapping = MODEL_MAP[option_type]
    model = mapping['model']
    field = mapping['field']
    try:
        options = model.query.order_by(db.func.lower(getattr(model, field))).all()
        options_list = [{'id': opt.id, 'value': getattr(opt, field)} for opt in options]
        return jsonify(options_list)
    except Exception as e:
        print(f"Error fetching options {option_type}: {e}")
        abort(500, description=f"Server error fetching options: {str(e)}")

@app.route('/delete_option/<option_type>/<int:option_id>', methods=['DELETE'])
@login_required
def delete_option(option_type, option_id):
    if option_type not in MODEL_MAP:
        abort(404, description="Option type not found.")
    mapping = MODEL_MAP[option_type]
    model = mapping['model']
    try:
        option_to_delete = db.session.get(model, option_id)
        if not option_to_delete:
            abort(404, description=f"{option_type.capitalize()} option with ID {option_id} not found.")
        field_value = getattr(option_to_delete, mapping['field'], '[unknown]')
        protected_options = {'reverseCharge': ['Yes', 'No'], 'gstin': ['N/A', 'URP'], 'gstout': ['Not Applicable']}
        if option_type in protected_options and field_value in protected_options[option_type]:
            return jsonify({"success": False, "message": f"Cannot delete core '{field_value}' option."}), 400
        db.session.delete(option_to_delete)
        db.session.commit()
        return jsonify({"success": True, "message": "Option deleted successfully."})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting {option_type} ID {option_id}: {e}")
        abort(500, description=f"Server error deleting option: {str(e)}")

# with app.app_context():
#     db.create_all()
#     add_initial_data()
