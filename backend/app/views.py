from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
import json
import pymongo
import datetime
import uuid     #for unique image name
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
        username = request.session['username']
        if username:
            data = {'status': 'error', 'message': 'Already logged in'}
            return JsonResponse(data)
        else:
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
                status = db.user_status.insert_one({"userId":data['username'], "status":"", "imagePath":""})
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
def fetch_posts(request):
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
def store_post(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            data=dict()
            data['userId'] = username
            data['caption'] = request.POST.get('caption')
            image = request.FILES.get('image')
            data['imagePath'] = store_image(image, 'post_images')
            data['postedAt'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            data['likes'] = 0
            insert_confirm = db.user_post.insert_one(data)
            if insert_confirm:
                data = {'status': 'success', 'message': 'Post created successfully'}
                return JsonResponse(data)
            else:
                data = {'status': 'error', 'message': 'Something went wrong'}
                return JsonResponse(data)
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

@csrf_exempt
def search(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            search_string=request.POST.get('search_string')
            search_list=[]
            search=db.user.find({"username":{'$regex':search_string, '$ne':username}}, {"_id":0, "username":1, "imagePath":1}).limit(10)
            for result in search:
                search_list.append(result)
            return JsonResponse(search_list, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def fetch_messages(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        targetId = request.POST.get('targetId')
        if username:
            messages_list=[]
            messages=db.user_message.find({"sourceId":username, "targetId":targetId}).limit(10)
            for message in messages:
                messages_list.append(message)
            return JsonResponse(messages_list, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def store_message(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            targetId = request.POST.get('targetId')
            message = request.POST.get('message')
            sentAt = datetime.datetime.now()
            messages=db.user_message.insert_one({"sourceId":username, "targetId":targetId, "message":message, "sentAt":sentAt})
            if messages:
                data = {'status': 'success', 'message': 'Message sent successfully'}
                return JsonResponse(data)
            else:
                data = {'status': 'error', 'message': 'Something went wrong'}
                return JsonResponse(data)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

def fetch_status(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            status=db.user_status.find({"userId":username}, {"_id":0})
            return JsonResponse(status, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

def store_status(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            image = request.FILE.get('image')
            imagePath = store_image(image, 'post_images')
            timeStamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            status = db.user.update_one({"username":username}, {"$set":{"imagePath":imagepath}})
            if status:
                data = {'status': 'success', 'message': 'Status updated successfully'}
                return JsonResponse(data)
            else:
                data = {'status': 'error', 'message': 'Something went wrong'}
                return JsonResponse(data)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def fetch_profile(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.session.get('username', False)
        if username:
            profile=db.user.find_one({"username":username}, {"_id":0})
            follower_count = count_followers(username)
            following_count = count_following(username)
            friend_count = count_friends(username)
            posts_count = count_posts(username)
            profile['follower_count']=follower_count
            profile['following_count']=following_count
            profile['friend_count']=friend_count
            profile['posts_count']=posts_count
            return JsonResponse(profile)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)



#plugins
def count_friends(username):
    friends=db.user_friend.find({"sourceId":username}).count()
    return friends

def count_followers(username):
    followers=db.user_follow.find({"targetId":username, "status":""}).count()
    return followers

def count_following(username):
    following=db.user_follow.find({"sourceId":username, "status":""}).count()
    return following

def count_posts(username):
    posts=db.user_post.find({"userId":username}).count()
    return posts

def store_image(image, subfolder):
    image_extention = image.name.split('.')[-1]
    image_name = str(uuid.uuid4()) + '.' + image_extention
    image_path = os.path.join(settings.MEDIA_ROOT, subfolder, image_name)
    with open(image_path, 'wb+') as file:
        for chunk in image.chunks():
            file.write(chunk)
    return image_path
    








