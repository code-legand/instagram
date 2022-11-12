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
    if request.method == 'POST' or request.method == 'GET':
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
    if request.method == 'POST' or request.method == 'GET':
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
    if request.method == 'POST' or request.method == 'GET':
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

@csrf_exempt
def get_posts(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            friends=db.user_friend.find({"sourceId":username}, {"_id":0, "targetId":1})
            followers=db.user_follower.find({"sourceId":username}, {"_id":0, "targetId":1})
            people = {username, *friends, *followers}      #starred
            people=list(people)
            posts = {}
            posts=db.user_post.find({"userId":{'$in':people}}, {"_id":0})
            data=[]
            for post in posts:
                data.append(post)
            # print(data)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def recommendations(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            friend_list=[]
            friends=db.user_friend.find({"sourceId":username}, {"_id":0, "targetId":1}).limit(10)
            for friend in friends:
                friend_list.append(friend['targetId'])
            friend_of_friend_list=[]
            friends_of_friends=db.user_friend.find({"sourceId":{'$in':friend_list}}, {"_id":0, "targetId":1}).limit(10)
            for friend in friends_of_friends:
                friend_of_friend_list.append(friend['targetId'])
            recommendation_list=[]
            recommendations=db.user.find({"username":{'$in':friend_list}, "username":{'$in':friend_of_friend_list}}, {"_id":0, "username":1, "imagePath":1}).limit(10)
            for recommendation in recommendations:
                recommendation_list.append(recommendation)
            return JsonResponse(recommendation_list, safe=False)

        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)



