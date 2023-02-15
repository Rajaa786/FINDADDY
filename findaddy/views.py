from traceback import print_tb
from django.contrib import auth
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
from decouple import config
from findaddy.banks.Axis import AXIS
from findaddy.banks.bob import BOB
from findaddy.banks.hdfc import HDFC # error
from findaddy.banks.icici import ICICI
from findaddy.banks.idfc import IDFC
from findaddy.banks.kotak import KOTAK
from findaddy.banks.pnb import PNB
from findaddy.banks.sbi import SBI
from findaddy.banks.union import UNION
from findaddy.banks.yesBank import YESBANK
import os
import json
import pandas as pd
import pyrebase


import warnings
warnings.filterwarnings('ignore')



config = {
    "apiKey": config('FIREBASE_APIKEY'),
    "authDomain": config('FIREBASE_AUTHDOMAIN'),
    "projectId": config('FIREBASE_PROJECTID'),
    "storageBucket": config('FIREBASE_STORAGEBUCKET'),
    "messagingSenderId": config('FIREBASE_MESSAGINGSENDERID'),
    "appId": config('FIREBASE_APPID'),
    "databaseURL": config('FIREBASE_DATABASEURL'),
}

firebase = pyrebase.initialize_app(config)
authe = firebase.auth()
db = firebase.database()
storage = firebase.storage()


# Create your views here.


def signIn(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    email = request.POST.get('email')
    pw = request.POST.get('pass')
    admin_cred = db.child("admin").get().val()
    if email == admin_cred['email'] and pw == admin_cred['password']:
        request.session['uid'] = 'admin'
        request.session['name'] = 'Admin'
        return render(request, 'admin/admin_dashboard.html')
    else:
        try:
            user = authe.sign_in_with_email_and_password(email, pw)
        except Exception as e:
            # message = "Invalid Credentials! Please Check your Email and Password."
            return render(request, "login.html", {"message": str(e)})
        info = authe.get_account_info(user['idToken'])
        if info['users'][0]['emailVerified'] == True:
            session_id = str(user['localId'])
            db.child('users').child("personal").child(
                session_id).update({"accstatus": "Active"})
            request.session['uid'] = session_id
            print('signed In successfully')
            result = check_plan(request)
            if result == 'success':
                return render(request, 'index.html')
            else:
                return render(request, 'index.html', {"message": result})
        else:
            return render(request, "login.html", {"message": "Please Verify your email."})


def reset(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    return render(request, "resetPassword.html")


def postReset(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    email = request.POST.get('email')
    try:
        authe.send_password_reset_email(email)
        return render(request, "confirmEmail.html", {"email": str(email)})
    except Exception as e:
        # message  = "Something went wrong, Please check the email you provided is registered or not"
        return render(request, "resetPassword.html", {"message": str(e)})


def logout(request):
    try:
        auth.logout(request)
    except:
        render(request, "index.html", {"message": "Logout Failed"})
    return render(request, "logout.html")


def signUp(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    company = request.POST.get('company')
    designation = request.POST.get('designation')
    plan = request.POST.get('plan')
    planstatus = 'Active'
    accstatus = 'Email Verification Pending'
    admin_days_limit = db.child("admin").child(
        "plan").child(plan).child("days_limit").get().val()
    createdate = timezone.now().isoformat()
    expirydate = timezone.now() + timedelta(days=admin_days_limit)
    expirydate = expirydate.isoformat()
    numreports = 0
    email = request.POST.get('email')
    pw = request.POST.get('pass')

    try:
        user = authe.create_user_with_email_and_password(email, pw)
        data = {"name": name, "email": email, "phone": phone, "company": company,
                "designation": designation, "plan": plan, "planstatus": planstatus,
                "accstatus": accstatus, "createdate": createdate, "expirydate": expirydate,
                "numreports": numreports}
        db.child("users").child("personal").child(
            str(user['localId'])).set(data)
        authe.send_email_verification(user['idToken'])

    except Exception as e:
        # message = "User already exists."
        return render(request, "register.html", {"message": str(e)})
    return render(request, "confirmEmail.html", {"email": str(email)})


def landing(request):
    if 'uid' in request.session:
        if request.session['uid'] == 'admin':
            return render(request, 'admin/admin_dashboard.html')
        print('checking plan...')
        result = check_plan(request)
        print(f'result:{result}')
        if result == 'not found':
            auth.logout(request)
            return render(request, 'login.html', {"message": "Please Login Again"})
        elif result == 'success':
            return render(request, 'index.html')
        else:
            return render(request, 'index.html', {"message": result})
    return render(request, 'landing.html')


def register(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    print(request.POST)
    if 'plan' in request.POST:
        plan = request.POST['plan']
    return render(request, 'register.html', {"plan": str(plan)})


def pricing(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    return render(request, 'pricing.html')


def login(request):
    if 'uid' in request.session:
        return render(request, 'index.html')
    return render(request, 'login.html')


def admin_dashboard(request):
    if check_login(request):
        if request.session['name'] == 'Admin':
            return render(request, 'admin/admin_dashboard.html')
    return render(request, 'login.html', {"message": "Please Login Again"})


def admin_view_users(request):
    if check_login(request):
        return render(request, 'admin/admin_view_users.html')
    return render(request, 'login.html', {"message": "Please Login Again"})


def admin_view_reports(request):
    if check_login(request):
        key = request.GET.get('key')
        return render(request, 'admin/admin_view_reports.html', {"key": key})
    return render(request, 'login.html', {"message": "Please Login Again"})


def admin_report_data(request):
    if check_login(request):
        key = request.GET.get('key')
        key_id = request.GET.get('key_id')
        return render(request, 'admin/admin_report_data.html', {"key": key, "key_id": key_id})
    return render(request, 'login.html', {"message": "Please Login Again"})


def admin_view_users_ajax(request):
    if check_login(request):
        reports = db.child("users").child("personal").get().val()
        if reports != None:
            return JsonResponse(reports)
        return JsonResponse({})
    return render(request, 'login.html', {"message": "Please Login Again"})


def admin_view_reports_ajax(request):
    key = request.GET.get('key')
    reports = db.child("users").child('reports').child(key).get().val()
    if reports != None:
        return JsonResponse(reports)
    return JsonResponse({})


def admin_report_data_ajax(request):
    key = request.GET.get('key')
    key_id = request.GET.get('key_id')
    report = db.child("users").child('tables').child(
        key).child(key_id).get().val()
    tables = dict(report)
    return JsonResponse(tables)


def createReport(request):
    if check_login(request):
        print('checking plan...')
        result = check_plan(request)
        print(f'result:{result}')
        if result == 'not found':
            auth.logout(request)
        elif result == 'success':
            return render(request, 'createReport.html')
        else:
            return render(request, 'index.html', {"message": result})
    return render(request, 'login.html', {"message": "Please Login Again"})


def create_report_ajax(request):

    # Checking Limit Value
    admin_report_limit = db.child("admin").child("plan").child(
        request.session["plan"]).child("report_limit").get().val()

    # Checking if limit is reached
    if request.session['numreports'] >= admin_report_limit:
        return HttpResponse('limit reached')

    # Setting up the report
    report = {}
    if request.method == 'POST':
        print('POST request received')
        report['reportname'] = str(request.POST.get('reportname'))
        report['bankname'] = str(request.POST.get('bankname'))
        report['accountType'] = str(request.POST.get('accountType'))
        report['accountNumber'] = str(request.POST.get('accountNumber'))
        report['pdfpassword'] = str(request.POST.get('pdfpassword'))
        report['startdate'] = str(request.POST.get('startdate'))
        report['enddate'] = str(request.POST.get('enddate'))
        pdf = request.FILES['accountStatement'].temporary_file_path()

        # Generating Excel Report
        try:
            print('Generating Excel Report....')
            if report['bankname'] == 'AXIS':
                AXIS(pdf, report['pdfpassword'],
                     report['startdate'], report['enddate'])
            elif report['bankname'] == 'ICICI':
                ICICI(pdf, report['pdfpassword'],
                      report['startdate'], report['enddate'])
            elif report['bankname'] == 'HDFC':
                HDFC(pdf, report['pdfpassword'],
                     report['startdate'], report['enddate'])
            elif report['bankname'] == 'KOTAK':
                KOTAK(pdf, report['pdfpassword'],
                      report['startdate'], report['enddate'])
            elif report['bankname'] == 'SBI':
                SBI(pdf, report['pdfpassword'],
                    report['startdate'], report['enddate'])
            elif report['bankname'] == 'IDFC':
                IDFC(pdf, report['pdfpassword'],
                     report['startdate'], report['enddate'])
            elif report['bankname'] == 'UNION':
                UNION(pdf, report['pdfpassword'],
                      report['startdate'], report['enddate'])
            elif report['bankname'] == 'YES':
                YESBANK(pdf, report['pdfpassword'],
                        report['startdate'], report['enddate'])
            elif report['bankname'] == 'BOB':
                BOB(pdf, report['pdfpassword'],
                    report['startdate'], report['enddate'])
            elif report['bankname'] == 'PNB':
                PNB(pdf, report['pdfpassword'],
                    report['startdate'], report['enddate'])
            else:
                print('Bank not supported')
                return HttpResponse('Error')
            print('Excel Report Generated Completely')
        except Exception as e:
            print('Excel Report Generation Failed')
            print(e)
            return HttpResponse('Error')

        # Checking if report is present or not
        report_loc = os.path.join(
            os.getcwd(), 'Excel_Files' + '/' + 'BankStatement.xlsx')
        folder_loc = os.path.join(
            os.getcwd(), 'Excel_Files')
        if not os.path.exists(folder_loc):
            print('Folder not found')
            return HttpResponse('Error')
        else:
            print('Folder found')
            print('Searching for xlsx file')
            file_loc = os.path.join(
                folder_loc, 'BankStatement.xlsx')
            if not os.path.exists(file_loc):
                print('File not found')
                return HttpResponse('Error')
            else:
                print('File found')

        # Converting Excel Report to JSON Format
        print('Converting Excel Report to JSON Format')
        tables = dict()
        try:
            xlsx_file = pd.ExcelFile(report_loc)
            xlsx_sheets = xlsx_file.sheet_names
            for sheet in xlsx_sheets:
                excel_data_df = pd.read_excel(report_loc, sheet_name=sheet)
                sheet_json = excel_data_df.to_json(orient='records')
                sheet_json = json.loads(sheet_json)
                tables[sheet] = json.dumps(sheet_json)
            print('Excel to JSON Conversion Complete')
        except Exception as e:
            print('Excel to JSON Conversion Failed')
            print(e)
            return HttpResponse('Error')

        # Uploading Excel Report to Firebase Storage
        today_date = str(datetime.now().strftime("%d-%m-%Y-%H%M%S"))
        storage_loc = os.path.join(
            request.session['uid'], 'reports' + '/' + today_date + '/' + report['reportname'] + '.xlsx')
        if os.path.exists(report_loc):
            print('Uploading Excel Report to Firebase Storage')
            try:
                storage.child(storage_loc).put(report_loc)
                excel_url = storage.child(storage_loc).get_url(None)
                print('Excel Report Uploaded Completely')
            except Exception as e:
                print('Excel Report Upload Failed')
                print(e)
                return HttpResponse('Error')
        else:
            print('Excel Report Not Found')
            return HttpResponse('Error')

        # Uploading JSON Report Tables to Firebase Database
        print('Uploading JSON Report Tables to Firebase Database')
        report_data = {
            'reportname': report['reportname'],
            'bankname': report['bankname'],
            'accountType': report['accountType'],
            'accountNumber': report['accountNumber'],
            'startdate': report['startdate'],
            'enddate': report['enddate'],
            'createdAt': today_date[0:10].replace("-", "/"),
            'excel_url': str(excel_url),
        }
        try:
            db.child("users").child('reports').child(
                request.session['uid']).child(today_date).set(report_data)
            db.child("users").child('tables').child(
                request.session['uid']).child(today_date).set(tables)
            print('Report JSON Uploaded Completely')
        except Exception as e:
            print('Report JSON Upload Failed')
            print(e)
            return HttpResponse('Error')

        # Incrementing Number of Reports
        print('Incrementing Number of Reports')
        request.session['numreports'] += 1
        db.child("users").child("personal").child(request.session['uid']).update(
            {"numreports": request.session['numreports']})

        print('Report Created and Uploaded Successfully')

        return HttpResponse(excel_url)

    # If request is not received as POST
    else:
        print('Request not received')
        return HttpResponse('Error')


def viewReport(request):
    if check_login(request):
        print('checking plan...')
        result = check_plan(request)
        print(f'result:{result}')
        if result == 'not found':
            auth.logout(request)
        elif result == 'success':
            return render(request, 'viewReport.html')
        else:
            return render(request, 'index.html', {"message": result})
    return render(request, 'login.html', {"message": "Please Login Again"})


def reports_ajax(request):
    reports = db.child("users").child('reports').child(
        request.session['uid']).get().val()
    if reports != None:
        return JsonResponse(reports)
    return JsonResponse({})


def showReport(request):
    if check_login(request):
        if check_plan_expired(request):
            query = request.GET.get('data')
            report = db.child("users").child('tables').child(
                request.session['uid']).child(query).get().val()
            tables = dict(report)
            return render(request, 'showReport.html', {'tables': tables})
        return render(request, 'index.html', {"message": "Your plan has expired"})
    return render(request, 'login.html', {"message": "Please Login Again"})


def check_plan(request):
    current = timezone.now()
    user = db.child("users").child("personal").child(
        request.session['uid']).get().val()
    if not user:
        return "not found"
    for key, value in user.items():
        request.session[key] = value
    expiry = datetime.fromisoformat(request.session['expirydate'])
    status = current < expiry
    if not status and request.session['accstatus'] == 'Active':
        db.child("users").child("personal").child(request.session['uid']).update(
            {"planstatus": "Expired"})
        request.session['planstatus'] = "Expired"
    admin_report_limit = db.child("admin").child("plan").child(
        request.session["plan"]).child("report_limit").get().val()
    if request.session['planstatus'] == 'Expired':
        return "Your plan has expired."
    elif request.session['numreports'] > admin_report_limit:
        return "You have exceeded the limit of reports."
    else:
        return "success"


def check_login(request):
    if 'uid' in request.session:
        return True
    return False


def check_plan_expired(request):
    if request.session['planstatus'] == 'Expired':
        return False
    return True
