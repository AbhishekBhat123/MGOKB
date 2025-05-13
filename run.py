# import os
# import datetime
# import json
# from io import BytesIO
# import re
# from flask import (Flask, render_template, request, jsonify, abort,
#                    session, redirect, url_for, flash, send_file, Blueprint)
# from flask_sqlalchemy import SQLAlchemy
# import openpyxl
# from openpyxl import Workbook, load_workbook
# from openpyxl.utils.exceptions import InvalidFileException
# import traceback

# # Authentication Imports
# from flask_login import (
#     LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# )
# from werkzeug.security import generate_password_hash, check_password_hash

 
# views = Blueprint('views', __name__)
# # --- App Initialization ---
# app = Flask(__name__)

# # IMPORTANT: Change this to a strong, random secret key!
# app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_insecure_default_secret_key_CHANGE_ME_NOW')

# # --- Database Configuration ---
# # basedir = os.path.abspath(os.path.dirname(__file__))
# # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'invoice_options.db')
# # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# # db = SQLAlchemy(app)
# basedir = '/tmp'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'invoice_options.db')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# # --- Create Output Directory ---
# # output_dir = os.path.join(basedir, 'output')
# # if not os.path.exists(output_dir):
# #     os.makedirs(output_dir)
# output_dir = '/tmp/output'
# if not os.path.exists(output_dir):
#     os.makedirs(output_dir)
# excel_log_file = os.path.join(output_dir, 'all_prints_log.xlsx')
# # --- Define the Excel Log File Path ---
# # excel_log_file = os.path.join(output_dir, 'all_prints_log.xlsx')

# # --- Define Headers for the Excel Log File ---
# EXCEL_LOG_HEADERS = [
#     "LogTimestamp", "InvoiceNumber", "DocumentType", "PrintDate", "Reference",
#     "Purpose", "Category", "BillingMonthYear", "GSTIN", "Billedto",
#     "PaymentMethod", "ReverseCharge", "AdvancePayment", "SubTotal",
#     "DiscountApplied", "DiscountPercentage", "DiscountAmount", "GrandTotal",
#     "LineItems_Count", "LineItems_CostCategories", "LineItems_Descriptions",
#     "LineItems_SACs", "LineItems_RatesAndUnits", "LineItems_ConsumedUnitsAndUnits", "LineItems_Totals"
# ]


# # --- Database Models ---
# class ReferenceOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     __tablename__ = 'reference_option'

# class PurposeOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     __tablename__ = 'purpose_option'

# class CategoryOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     __tablename__ = 'category_option'

# class GstinOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     value = db.Column(db.String(15), unique=True, nullable=False)
#     __tablename__ = 'gstin_option'

# class GstoutOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     value = db.Column(db.String(15), unique=True, nullable=False)
#     __tablename__ = 'gstout_option'

# class DescriptionOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(200), unique=True, nullable=False)
#     __tablename__ = 'description_option'

# class SacOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     code = db.Column(db.String(10), unique=True, nullable=False)
#     __tablename__ = 'sac_option'

# class ReverseChargeOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     value = db.Column(db.String(5), unique=True, nullable=False)
#     __tablename__ = 'reverse_charge_option'

# class PaymentMethodOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     __tablename__ = 'payment_method_option'

# class CostCategoryOption(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     __tablename__ = 'cost_category_option'

# # --- NEW Database Model for Invoice Sequence ---
# class InvoiceSequence(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(50), unique=True, nullable=False) # Link to Flask-Login user ID
#     fixed_prefix = db.Column(db.String(100), nullable=False) # e.g., "MGKBIN-BioNEST "
#     fixed_code = db.Column(db.String(50), nullable=False) # e.g., "4661" (client should send this without trailing slash)
#     financial_year = db.Column(db.String(10), nullable=False) # e.g., "2024-25"
#     last_number = db.Column(db.Integer, default=0, nullable=False) # The last number assigned for this user

#     __tablename__ = 'invoice_sequence'


# # --- Model Mapping Dictionary ---
# MODEL_MAP = {
#     'reference': {'model': ReferenceOption, 'field': 'name'},
#     'purpose': {'model': PurposeOption, 'field': 'name'},
#     'category': {'model': CategoryOption, 'field': 'name'},
#     'gstin': {'model': GstinOption, 'field': 'value'},
#     'gstout': {'model': GstoutOption, 'field': 'value'},
#     'itemDescription': {'model': DescriptionOption, 'field': 'name'},
#     'itemSac': {'model': SacOption, 'field': 'code'},
#     'reverseCharge': {'model': ReverseChargeOption, 'field': 'value'},
#     'paymentMethod': {'model': PaymentMethodOption, 'field': 'name'},
#     'costCategory': {'model': CostCategoryOption, 'field': 'name'},
# }

# # --- Flask-Login Configuration ---
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'
# login_manager.login_message_category = "info"

# # --- User Representation (NOT FOR PRODUCTION USE) ---
# class User(UserMixin):
#     def __init__(self, id, username, password_hash):
#         self.id = id
#         self.username = username
#         self.password_hash = password_hash

#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)

# users_db = {
#     "1": User(id="1", username="admin", password_hash=generate_password_hash("password123")),
#     "2": User(id="2", username="user", password_hash=generate_password_hash("test")),
#     "3": User(id="3", username="Abhi", password_hash=generate_password_hash("test123")),
# }

# @login_manager.user_loader
# def load_user(user_id):
#     """Required callback for Flask-Login."""
#     return users_db.get(user_id)

# # --- Helper Function to calculate Indian Financial Year ---
# def get_indian_financial_year(date=None):
#     """Calculates the Indian Financial Year (Apr-Mar) for a given date."""
#     if date is None:
#         date = datetime.date.today()
#     year = date.year
#     month = date.month

#     if month < 4: # Before April
#         financial_year_start = year - 1
#         financial_year_end = year
#     else: # April or later
#         financial_year_start = year
#         financial_year_end = year + 1

#     # Format as "YYYY-YY"
#     return f"{financial_year_start}-{str(financial_year_end)[-2:]}"


# # --- Helper Function to Add Initial Data ---
# def add_initial_data():
#     initial_data = {
#         ReferenceOption: ["Ref001", "Ref002", "Project X", "Support Ticket"],
#         PurposeOption: ["Consulting Services", "Software Development", "Annual Maintenance", "Training"],
#         CategoryOption: ["Software License", "Hardware Sale", "Professional Services", "Subscription"],
#         GstoutOption: ["30KLMNO9876P1Z0", "31QRSTU5432V1ZA", "Not Applicable"],
#         GstinOption: ["29ABCDE1234F1Z5", "27FGHIJ5678K1Z9", "N/A", "URP"],
#         DescriptionOption: ["Web Development Hours", "API Integration Setup", "Server Maintenance (Monthly)", "Consulting Call"],
#         SacOption: ["998314", "998315", "998319", "998311"],
#         ReverseChargeOption: ["Yes", "No"],
#         PaymentMethodOption: ["Bank Transfer (NEFT/RTGS)", "Credit Card", "UPI", "Cheque"],
#         CostCategoryOption: ["Travel", "Accommodation", "Software", "Hardware", "Services", "Miscellaneous"]
#     }
#     with app.app_context():
#         # This will create all tables, including the new InvoiceSequence table
#         db.create_all()
#         needs_commit = False
#         for model, items in initial_data.items():
#             try:
#                 # Only populate if the table is empty
#                 if model.query.count() == 0:
#                     print(f"Populating initial data for {model.__tablename__}...")
#                     needs_commit = True
#                     field_name = None
#                     if hasattr(model, 'name'): field_name = 'name'
#                     elif hasattr(model, 'value'): field_name = 'value'
#                     elif hasattr(model, 'code'): field_name = 'code'

#                     if field_name:
#                         for item in items:
#                             record = model(**{field_name: item})
#                             db.session.add(record)
#                     else:
#                         print(f"Warning: Could not determine field name for model {model.__name__}")
#             except Exception as e:
#                 print(f"Error querying or populating {model.__name__}: {e}")

#         if needs_commit:
#             try:
#                 db.session.commit()
#                 print("Initial data committed.")
#             except Exception as e:
#                 db.session.rollback()
#                 print(f"Error committing initial data: {e}")
#         else:
#             print("Initial data already exists or no data to add.")


# # --- Helper Function to add a new option ---
# def add_new_option_if_needed(option_type, selected_value, new_value_str):
#     """
#     Checks if a new option needs to be added based on form selection and input.
#     Adds to DB session if new and unique.
#     Returns a tuple: (was_added_to_session: bool, final_resolved_value: str).
#     """
#     # If 'Add New' wasn't selected, just return the selected value.
#     if selected_value != 'Add New':
#         return False, selected_value

#     # User selected 'Add New'. Process the provided new value string.
#     new_value = (new_value_str or '').strip()

#     # If no new value was provided or it's empty after stripping
#     if not new_value:
#         # Return 'Add New' as the resolved value, indicating nothing specific was chosen.
#         return False, 'Add New'

#     # Check if the option_type is valid
#     if option_type not in MODEL_MAP:
#         print(f"Warning: Unknown option type '{option_type}' for adding.")
#         # Cannot add, return the value the user typed
#         return False, new_value

#     mapping = MODEL_MAP[option_type]
#     model = mapping['model']
#     field = mapping['field']

#     try:
#         # Check if the value already exists in the database
#         exists = model.query.filter(getattr(model, field) == new_value).first()

#         if not exists:
#             # Value does not exist, add it to the session.
#             new_record = model(**{field: new_value})
#             db.session.add(new_record)
#             # Return True (indicating added to session) and the new value
#             return True, new_value
#         else: 
#             return False, getattr(exists, field)

#     except Exception as e:
#         # Error during database query or session add.
#         print(f"Error processing new {option_type} '{new_value}': {e}") 
#         return False, new_value


# # --- Helper to flatten line items for Excel Log ---
# def flatten_line_items(line_items):
#     """Flattens line items into semicolon-separated strings for logging."""
#     if not line_items:
#         return 0, "", "", "", "", "", "" # Return defaults if no items

#     count = len(line_items)
#     cost_categories = "; ".join([str(item.get('costCategory', '')) for item in line_items])
#     descriptions = "; ".join([str(item.get('description', '')) for item in line_items])
#     sacs = "; ".join([str(item.get('sac', '')) for item in line_items])
#     # Combine rate value and unit
#     rates = "; ".join([f"{item.get('rateValue', '')} per {item.get('rateUnit', '')}" for item in line_items])
#     # Combine units consumed value and unit
#     units = "; ".join([f"{item.get('unitsConsumedValue', '')} {item.get('unitsConsumedUnit', '')}" for item in line_items])
#     totals = "; ".join([str(item.get('total', '')) for item in line_items])

#     return count, cost_categories, descriptions, sacs, rates, units, totals


# # --- Authentication Routes ---
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     """Handles user login."""
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))

#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#         remember = True if request.form.get('remember') else False

#         user_found = None
#         for user in users_db.values():
#             if user.username.lower() == username.lower():
#                 user_found = user
#                 break

#         if user_found and user_found.check_password(password):
#             login_user(user_found, remember=remember)
#             flash('Logged in successfully.', 'success')
#             next_page = request.args.get('next')
#             return redirect(next_page or url_for('index'))
#         else:
#             flash('Invalid username or password.', 'danger')

#     return render_template('login.html')


# @app.route('/logout')
# @login_required
# def logout():
#     """Handles user logout."""
#     logout_user()
#     flash('You have been logged out.', 'success')
#     return redirect(url_for('login'))


# # --- Application Routes (Protected) ---

# @app.route('/')
# @login_required
# def index():
#     """Renders the main invoice/quote form page, loading data from DB."""
#     db_data = {}
#     try:
#         for key, mapping in MODEL_MAP.items():
#             model = mapping['model']
#             field = mapping['field']
#             # Order alphabetically, handling case by converting to lower for sorting
#             options = model.query.order_by(db.func.lower(getattr(model, field))).all()
#             db_data[key + '_options'] = options
#     except Exception as e:
#         print(f"Error loading options from database: {e}")
#         traceback.print_exc() # Add traceback for better debugging
#         # Provide empty lists on error so template rendering doesn't fail
#         for key in MODEL_MAP.keys():
#             db_data[key + '_options'] = []
    
#      # Get preview data from session without clearing it here
#     preview_data = session.get('preview_data', None)

#     return render_template('index3.html', data=db_data,  preview_data_json=json.dumps(preview_data))


# @app.route('/generate', methods=['POST'])
# @login_required
# def generate_document():
#     """Handles form submission, processes data, adds new options, and redirects to preview."""
#     if not request.is_json:
#         return jsonify({"error": "Request must be JSON"}), 400

#     form_data = request.get_json()
#     processed_form_data = {}
#     db_commit_needed = False
 
#     fields_to_check = [
#         'reference', 'purpose', 'category', 'gstin', 'gstout',
#         'reverseCharge', 'paymentMethod', 'costCategory' # costCategory check applies to line items too
#     ]

#     for field_key in fields_to_check:
#         # Keys from JS form data
#         selected_key = f'{field_key}Selected'
#         new_value_key = f'new{field_key.capitalize()}' # e.g., newReference

#         selected_value = form_data.get(selected_key)
#         new_value_str = form_data.get(new_value_key, '')

#         # Only attempt to process if the selected_key was present in the form data
#         if selected_key in form_data:
#             added, final_value = add_new_option_if_needed(field_key, selected_value, new_value_str)
#             db_commit_needed = db_commit_needed or added
#             processed_form_data[field_key] = final_value # Store the final resolved value
#         # else: field is not in form data, it won't be in processed_form_data


#     # Add other direct fields from the form
#     processed_form_data['docType'] = form_data.get('docType')
#     processed_form_data['monthYear'] = form_data.get('monthYear')
#     processed_form_data['applyDiscount'] = form_data.get('applyDiscount')
#     processed_form_data['discountPercentage'] = form_data.get('discountPercentage')
#     processed_form_data['advancePayment'] = form_data.get('advancePayment')
#     processed_form_data['subTotal'] = form_data.get('subTotal')
#     processed_form_data['discountAmount'] = form_data.get('discountAmount')
#     processed_form_data['grandTotal'] = form_data.get('grandTotal')
#     processed_form_data['billedTo'] = form_data.get('billedTo') # Include billedTo which is a free-text field

#     # Process Line Item Fields (checking if new options need adding for item fields)
#     processed_line_items = []
#     if 'lineItems' in form_data:
#         # Mapping from JS item key to MODEL_MAP key
#         line_item_fields_to_add_option = {
#             'costCategory': 'costCategory', # Note: costCategory is also a top-level field
#             'description': 'itemDescription',
#             'sac': 'itemSac',
#             # rate and unit are not options to add dynamically
#         }
#         for item in form_data['lineItems']:
#             processed_item = item.copy()
#             for item_field_key, option_type in line_item_fields_to_add_option.items():
#                  item_value = item.get(item_field_key, '')
#                  # Only attempt to add if the value is not empty and type is managed
#                  if item_value and option_type in MODEL_MAP: 
#                       added, final_item_value = add_new_option_if_needed(option_type, 'Add New', item_value)
#                       db_commit_needed = db_commit_needed or added
#                       processed_item[item_field_key] = final_item_value # Store the resolved value

#             processed_line_items.append(processed_item)
#     processed_form_data['lineItems'] = processed_line_items

#     # Commit new options if any were added
#     if db_commit_needed:
#         try:
#             db.session.commit()
#             print("New options committed.") # Log success
#         except Exception as e:
#             db.session.rollback()
#             print(f"Error committing new options: {e}")
#             flash(f'Error saving new options: {e}', 'danger')
#     if 'invoiceNumber' in processed_form_data:
#         del processed_form_data['invoiceNumber']
#     if 'currentDate' in processed_form_data:
#          del processed_form_data['currentDate']

#     session['preview_data'] = processed_form_data

#     # Return redirect instruction to the frontend JS
#     return jsonify({"redirect": url_for('preview_page')})


# @app.route('/preview')
# @login_required
# def preview_page():
#     """Displays the generated document preview using data from the session."""
#     preview_data = session.get('preview_data')

#     if not preview_data:
#         flash('No preview data found or session expired. Please generate the document again.', 'warning')
#         return redirect(url_for('index'))
#     # return render_template('preview2a2.html', preview_data=preview_data)
#     return render_template('test2_updated.html', preview_data=preview_data)


# @app.route('/edit')
# @login_required
# def edit_from_preview():
#     """Clears preview data from session and redirects back to the main form."""
#     session.pop('preview_data', None) # Remove preview data
#     flash('Returning to form. Please make your changes and regenerate.', 'info')
#     return redirect(url_for('index'))
# @app.route('/delete_preview', methods=['POST'])
# @login_required
# def delete_preview():
#     session.pop('preview_data', None)
#     flash('Document data cleared. Please fill the form again.', 'info')
#     return jsonify({"redirect": url_for('index')})
    
# # --- New route to clear session data after JS reads it ---
# @app.route('/clear_preview_data', methods=['POST'])
# @login_required
# def clear_preview_data():
#     """Clears the preview data from the session."""
#     session.pop('preview_data', None)
#     print("Preview data cleared from session.")
#     return jsonify({"success": True, "message": "Preview data cleared."})

# @app.route('/preview/<doc_id>')
# def preview_document(doc_id):
#     # Fetch document from database using doc_id
#     # return render_template("preview.html", document=doc)
#      doc_type = request.args.get('docType')

# # --- Invoice Sequence Management Routes ---

# # Renamed from assign_invoice_number
# @app.route('/get_invoice_sequence_info', methods=['GET'])
# @login_required
# def get_invoice_sequence_info():
#     """
#     Fetches the user's invoice sequence details (prefix, code, year, last number).
#     Handles financial year rollover by resetting the number in the DB if needed.
#     Does NOT increment the last_number for assignment. Returns info for display.
#     """
#     user_id = current_user.id
#     current_financial_year = get_indian_financial_year()

#     try:
#         sequence = InvoiceSequence.query.filter_by(user_id=user_id).first()

#         if not sequence:
#             # Sequence not set up for this user
#             print(f"Sequence setup needed for user {user_id}")
#             return jsonify({"status": "needs_setup", "financialYear": current_financial_year})

#         # Check if financial year matches the current year
#         if sequence.financial_year != current_financial_year: 
#             print(f"Financial year changed for user {user_id}. Resetting sequence.")
#             sequence.last_number = 0
#             sequence.financial_year = current_financial_year
#             db.session.commit() 
#         prefix_part = sequence.fixed_prefix.strip()
#         code_part = sequence.fixed_code.strip()
#         year_part = sequence.financial_year
#         next_num_pred = sequence.last_number + 1

#         # Construct the format example string carefully
#         format_example = f"{prefix_part}/{year_part}/{code_part}/{next_num_pred}"


#         return jsonify({
#             "status": "info",
#             "fixedPrefix": prefix_part,
#             "fixedCode": code_part,
#             "financialYear": year_part,
#             "lastNumber": sequence.last_number, # Return the last assigned number
#             "nextNumberPrediction": next_num_pred, # Predict the next number for display
#             "formatExample": format_example # Provide format example
#         })

#     except Exception as e:
#         db.session.rollback()  
#         print(f"Error getting invoice sequence info for user {user_id}: {e}")
#         traceback.print_exc()
#         return jsonify({"status": "error", "message": f"Server error getting sequence info: {str(e)}"}), 500


# @app.route('/setup_invoice_sequence', methods=['POST'])
# @login_required
# def setup_invoice_sequence():
#     """
#     Sets up the invoice sequence for the current user based on parts provided by the client.
#     Receives fixed_prefix, fixed_code, and starting_number.
#     The financial year is determined by the server.
#     """
#     user_id = current_user.id
#     data = request.get_json()

#     if not data:
#          return jsonify({"success": False, "message": "No data received."}), 400

#     fixed_prefix = data.get('fixedPrefix') # e.g., "MGKBIN-BioNEST "
#     fixed_code = data.get('fixedCode')     # e.g., "4661" (client should NOT send trailing slash now)
#     starting_number = data.get('startingNumber')

#     if fixed_prefix is None or fixed_code is None or starting_number is None: # Check for None explicitly
#          return jsonify({"success": False, "message": "Fixed prefix, fixed code, and starting number are required."}), 400

#     try:
#         starting_number = int(starting_number)
#         if starting_number < 0:
#              raise ValueError("Negative number not allowed.")
#     except ValueError:
#          return jsonify({"success": False, "message": "Starting number must be a non-negative integer."}), 400

#     # Check if sequence already exists for this user
#     existing_sequence = InvoiceSequence.query.filter_by(user_id=user_id).first()
#     if existing_sequence:
#         # This shouldn't ideally be reached if the client checks 'needs_setup' first,
#         # but handle defensively.
#         print(f"Setup attempted but sequence already exists for user {user_id}")
#         return jsonify({"success": False, "message": "Invoice sequence already exists for this user."}), 409 # Use 409 Conflict

#     current_financial_year = get_indian_financial_year()

#     # Save the new sequence
#     new_sequence = InvoiceSequence(
#         user_id=user_id,
#         fixed_prefix=fixed_prefix.strip(), # Save stripped value
#         fixed_code=fixed_code.strip(),     # Save stripped value (without client-provided slash)
#         financial_year=current_financial_year,
#         last_number=starting_number - 1 # Store the *last* number, so the first assigned is starting_number (e.g., if start is 40, last is 39)
#     )

#     try:
#         db.session.add(new_sequence)
#         db.session.commit()
#         print(f"Invoice sequence setup successfully for user {user_id} with prefix '{new_sequence.fixed_prefix}', code '{new_sequence.fixed_code}', year '{new_sequence.financial_year}', starting number {starting_number}.")
#         return jsonify({"success": True, "message": "Invoice sequence set up successfully."})
#     except Exception as e:
#         db.session.rollback() # Ensure rollback on error
#         print(f"Error setting up invoice sequence for user {user_id}: {e}")
#         traceback.print_exc()
#         return jsonify({"success": False, "message": f"Server error setting up sequence: {str(e)}"}), 500

# @app.route('/log_document_to_excel', methods=['POST'])
# @login_required
# def log_document_to_excel():
#     """
#     Receives document data, assigns the next invoice number based on the sequence,
#     allowing for manual override if provided. Uses manual date if provided, else current date.
#     Increments the sequence number, logs data to Excel, and returns the assigned invoice number and date.
#     """
#     data = request.get_json()
#     if not data:
#         return jsonify({"success": False, "message": "No data received."}), 400

#     user_id = current_user.id
#     current_financial_year = get_indian_financial_year()
#     invoice_number_to_log = 'ASSIGNMENT_FAILED'  # Default in case of error
#     log_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     # Use manual date if provided, else use current date
#     manual_date = data.get('manualDate')
#     if manual_date and validate_date(manual_date):
#         print_date = manual_date
#         print(f"User {user_id} provided manual date: {print_date}")
#     else:
#         print_date = datetime.datetime.now().strftime("%Y-%m-%d")
#         if manual_date:
#             print(f"Warning: Invalid manual date provided by user {user_id}: '{manual_date}'")

#     manual_number_part_str = data.get('manualInvoiceNumberPart')
#     manual_number_part = None

#     if manual_number_part_str:
#         try:
#             manual_number_part = int(manual_number_part_str)
#             if manual_number_part <= 0:
#                 raise ValueError("Manual number must be positive.")
#             print(f"User {user_id} provided manual number part: {manual_number_part}")
#         except (ValueError, TypeError) as e:
#             print(f"Warning: Invalid manual number part provided by user {user_id}: '{manual_number_part_str}' - {e}")
#             manual_number_part = None

#     try:
#         # --- 1. Determine/Assign the Invoice Number ---
#         sequence = InvoiceSequence.query.filter_by(user_id=user_id).with_for_update().first()

#         if not sequence:
#             print(f"Log attempt failed: Sequence setup needed for user {user_id}")
#             db.session.rollback()
#             return jsonify({"status": "needs_setup"})

#         # Handle financial year change
#         if sequence.financial_year != current_financial_year:
#             print(f"Financial year changed for user {user_id}. Resetting sequence.")
#             sequence.last_number = 0
#             sequence.financial_year = current_financial_year
#             db.session.commit()
#             sequence = InvoiceSequence.query.filter_by(user_id=user_id).with_for_update().first()

#         assigned_number_part = sequence.last_number + 1  # Default: next sequential number
#         used_manual_number = False

#         if manual_number_part is not None:
#             assigned_number_part = manual_number_part
#             used_manual_number = True
#             # Update sequence.last_number to the higher of manual_number_part or sequence.last_number + 1
#             sequence.last_number = max(manual_number_part, sequence.last_number + 1)
#             print(f"User {user_id} used manual number {manual_number_part}. Sequence last_number updated to {sequence.last_number}.")
#         else:
#             # Default case: use next number and increment sequence
#             sequence.last_number = assigned_number_part
#             print(f"User {user_id} assigned sequential number {assigned_number_part}. Sequence last_number updated to {sequence.last_number}.")

#         # Commit the sequence update
#         db.session.commit()

#         # Construct the final invoice number
#         prefix_part = sequence.fixed_prefix.strip()
#         code_part = sequence.fixed_code.strip()
#         year_part = sequence.financial_year
#         invoice_number_to_log = f"{prefix_part}/{year_part}/{code_part}/{assigned_number_part:04d}"
#         print(f"Final number for logging: {invoice_number_to_log} for user {user_id}")

#         # --- 2. Log Data to Excel ---
#         workbook = None
#         worksheet = None
#         log_file_path = excel_log_file  # Ensure this is defined in your config
#         write_header = not os.path.exists(log_file_path)

#         if not write_header:
#             try:
#                 workbook = load_workbook(log_file_path)
#                 worksheet = workbook.active
#                 current_headers = [cell.value for cell in worksheet[1]]
#                 if current_headers != EXCEL_LOG_HEADERS:
#                     print(f"Warning: Headers in '{log_file_path}' do not match expected. Found: {current_headers[:5]}... Expected: {EXCEL_LOG_HEADERS[:5]}...")
#             except (InvalidFileException, FileNotFoundError) as e:
#                 print(f"Warning: Log file '{log_file_path}' load error ({type(e).__name__}). Creating a new one.")
#                 write_header = True
#             except Exception as e:
#                 print(f"Error loading existing log file '{log_file_path}': {e}")
#                 traceback.print_exc()
#                 write_header = True

#         if write_header or worksheet is None:
#             workbook = Workbook()
#             worksheet = workbook.active
#             worksheet.append(EXCEL_LOG_HEADERS)
#             print(f"Created new Excel log file: {log_file_path}")

#         line_items = data.get('lineItems', [])
#         (item_count, item_cats, item_descs, item_sacs,
#          item_rates, item_units, item_totals) = flatten_line_items(line_items)

#         row_data = [
#             log_timestamp,
#             invoice_number_to_log,
#             data.get('docType', 'N/A').upper(),
#             print_date,
#             data.get('reference', 'N/A'),
#             data.get('purpose', 'N/A'),
#             data.get('category', 'N/A'),
#             data.get('monthYear', 'N/A'),
#             data.get('gstin', 'N/A'),
#             data.get('gstout', 'N/A'),
#             data.get('paymentMethod', 'N/A'),
#             data.get('reverseCharge', 'N/A'),
#             'Yes' if data.get('advancePayment') else 'No',
#             data.get('subTotal', 0.0),
#             'Yes' if data.get('applyDiscount') else 'No',
#             data.get('discountPercentage', 0.0) if data.get('applyDiscount') else 0.0,
#             data.get('discountAmount', 0.0) if data.get('applyDiscount') else 0.0,
#             data.get('grandTotal', 0.0),
#             item_count,
#             item_cats,
#             item_descs,
#             item_sacs,
#             item_rates,
#             item_units,
#             item_totals
#         ]

#         worksheet.append(row_data)
#         workbook.save(log_file_path)
#         print(f"Successfully logged invoice {invoice_number_to_log} to Excel for user {user_id}.")

#         # --- 3. Update Session and Return ---
#         if 'preview_data' in session and isinstance(session['preview_data'], dict):
#             session['preview_data']['invoiceNumber'] = invoice_number_to_log
#             session['preview_data']['currentDate'] = print_date
#             session.modified = True

#         return jsonify({
#             "success": True,
#             "invoiceNumber": invoice_number_to_log,
#             "currentDate": print_date,
#             "usedManualNumber": used_manual_number
#         })

#     except Exception as e:
#         db.session.rollback()
#         print(f"CRITICAL Error during log/assignment for user {user_id} (invoice: {invoice_number_to_log}): {e}")
#         traceback.print_exc()
#         return jsonify({"success": False, "message": f"Server error logging data or assigning number: {str(e)}"}), 500

# def validate_date(date_str):
#     """Validates if the date string is in YYYY-MM-DD formate and is a valid date."""
#     try:
#         datetime.datetime.strptime(date_str, "%Y-%m-%d")
#         return True
#     except ValueError:
#         return False

# @app.route('/get_options/<option_type>', methods=['GET'])
# @login_required
# def get_options(option_type):
#     """Fetches options for a given type from the database."""
#     if option_type not in MODEL_MAP:
#         abort(404, description="Option type not found.")
#     mapping = MODEL_MAP[option_type]
#     model = mapping['model']
#     field = mapping['field']
#     try:
#         # Order alphabetically, case-insensitive
#         options = model.query.order_by(db.func.lower(getattr(model, field))).all()
#         options_list = [{'id': opt.id, 'value': getattr(opt, field)} for opt in options]
#         return jsonify(options_list)
#     except Exception as e:
#         print(f"Error fetching options {option_type}: {e}")
#         abort(500, description=f"Server error fetching options: {str(e)}")
    
# @app.route('/delete_option/<option_type>/<int:option_id>', methods=['DELETE'])
# @login_required
# def delete_option(option_type, option_id):
#     """Deletes a specific option by type and ID."""
#     if option_type not in MODEL_MAP: abort(404, description="Option type not found.")
#     mapping = MODEL_MAP[option_type]
#     model = mapping['model']
#     try:
#         option_to_delete = db.session.get(model, option_id)
#         if not option_to_delete:
#              abort(404, description=f"{option_type.capitalize()} option with ID {option_id} not found.")

#         field_value = getattr(option_to_delete, mapping['field'], '[unknown]')

#         # Define protected options (values that cannot be deleted)
#         protected_options = {'reverseCharge': ['Yes', 'No'], 'gstin': ['N/A', 'URP'], 'gstout': ['Not Applicable']}
#         if option_type in protected_options and field_value in protected_options[option_type]:
#              return jsonify({"success": False, "message": f"Cannot delete core '{field_value}' option."}), 400

#         db.session.delete(option_to_delete)
#         db.session.commit()
#         return jsonify({"success": True, "message": "Option deleted successfully."})
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error deleting {option_type} ID {option_id}: {e}")
#         abort(500, description=f"Server error deleting option: {str(e)}")

# with app.app_context():
#     db.create_all()
#     add_initial_data()



# Testing


import os
import datetime
import json
from io import BytesIO
import re
from flask import (Flask, render_template, request, jsonify, abort,
                   session, redirect, url_for, flash, send_file, Blueprint)
from flask_sqlalchemy import SQLAlchemy
import openpyxl
from openpyxl import Workbook
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

views = Blueprint('views', __name__)
app = Flask(__name__)

# --- App Configuration ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_insecure_default_secret_key_CHANGE_ME_NOW')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
            print(f"Warning: Invalid manual number part provided by user {user_id}: '{manual_number_part_str}' - {e}")
            manual_number_part = None
    try:
        sequence = InvoiceSequence.query.filter_by(user_id=user_id).with_for_update().first()
        if not sequence:
            print(f"Log attempt failed: Sequence setup needed for user {user_id}")
            db.session.rollback()
            return jsonify({"status": "needs_setup"})
        if sequence.financial_year != current_financial_year:
            print(f"Financial year changed for user {user_id}. Resetting sequence.")
            sequence.last_number = 0
            sequence.financial_year = current_financial_year
            db.session.commit()
            sequence = InvoiceSequence.query.filter_by(user_id=user_id).with_for_update().first()
        assigned_number_part = sequence.last_number + 1
        if manual_number_part is not None:
            assigned_number_part = manual_number_part
            used_manual_number = True
            sequence.last_number = max(manual_number_part, sequence.last_number + 1)
            print(f"User {user_id} used manual number {manual_number_part}. Sequence last_number updated to {sequence.last_number}.")
        else:
            sequence.last_number = assigned_number_part
            print(f"User {user_id} assigned sequential number {assigned_number_part}. Sequence last_number updated to {sequence.last_number}.")
        db.session.commit()
        prefix_part = sequence.fixed_prefix.strip()
        code_part = sequence.fixed_code.strip()
        year_part = sequence.financial_year
        invoice_number_to_log = f"{prefix_part}/{year_part}/{code_part}/{assigned_number_part:04d}"
        print(f"Final number for logging: {invoice_number_to_log} for user {user_id}")
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
        print(f"Successfully logged invoice {invoice_number_to_log} to database for user {user_id}.")
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
        print(f"CRITICAL Error during log/assignment for user {user_id} (invoice: {invoice_number_to_log}): {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error logging data or assigning number: {str(e)}"}), 500

@app.route('/download_invoice_log', methods=['GET'])
@login_required
def download_invoice_log():
    try:
        logs = InvoiceLog.query.filter_by(user_id=current_user.id).order_by(InvoiceLog.log_timestamp).all()
        if not logs:
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
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'invoice_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        print(f"Error generating Excel download for user {current_user.id}: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error generating Excel file: {str(e)}"}), 500

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

with app.app_context():
    db.create_all()
    add_initial_data()
