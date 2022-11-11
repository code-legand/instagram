from django.shortcuts import render, redirect, HttpResponse

from django.http import JsonResponse
import json
import pymongo
import datetime
from django.views.decorators.csrf import csrf_exempt

client = pymongo.MongoClient("mongodb+srv://user:user@cluster0.ii2taey.mongodb.net/?retryWrites=true&w=majority")
db = client.instagram

# Create your views here.
@csrf_exempt
def home(request):
    data = {'status': 'success'}
    return JsonResponse(data)

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        data=dict()
        data['email'] = request.POST.get('email')
        data['fullname'] = request.POST.get('fullname')
        data['username'] = request.POST.get('username')
        data['password'] = request.POST.get('password')
        
        check1 = db.user.find_one({'email': data['email']})
        check2 = db.user.find_one({'username': data['username']})
        if check1:
            data = {'status': 'error', 'message': 'Email already exists'}
            return JsonResponse(data)
        elif check2:
            data = {'status': 'error', 'message': 'Username already exists'}
            return JsonResponse(data)
        else:
            data['type'] = 'public'
            data['registeredAt'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.f%z")
            data['lastLogin'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            insert_confirm = db.user.insert_one(data)
            if insert_confirm:
                request.session['username'] = data['username']
                data = {'status': 'success', 'message': 'User created successfully'}
                return JsonResponse(data)
            else:
                data = {'status': 'error', 'message': 'Something went wrong'}
                return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)


@csrf_exempt
def login(request):
    if request.method == 'POST' :
        username = request.session.get('username', False)
        if username:
            data = {'status': 'error', 'message': 'Already logged in'}
            return JsonResponse(data)
        else:
            data = {}
            data['username'] = request.POST.get('username')
            data['password'] = request.POST.get('password')
            check = db.user.find_one({'username': data['username'], 'password': data['password']})
            if check:
                request.session['username'] = data['username']
                print(request.session['username'])
                data = {'status': 'success', 'message': 'Login successful'}
                return JsonResponse(data)
            else:
                data = {'status': 'error', 'message': 'Invalid credentials'}
                return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def logout(request):
    if request.method == 'POST' :
        username = request.session.get('username', False)
        if username:
            request.session.flush()
            data = {'status': 'success', 'message': 'Logout successful'}
            return JsonResponse(data)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)