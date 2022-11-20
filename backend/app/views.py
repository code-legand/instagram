from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse, FileResponse
from backend import settings
import json
import pymongo
import dns
import datetime
import uuid     #for unique image name
import os
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
        print(data)
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
            data['registeredAt'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            data['lastLogin'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            insert_confirm = db.user.insert_one(data)
            status = db.user_status.insert_one({"userId":data['username'], "status":"", "imagePath":""})
            if insert_confirm:
                # request.session['username'] = data['username']
                db.user_logged.insert_one({"username":data['username'], "status":0})
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
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            data = {'status': 'error', 'message': 'Already logged in'}
            return JsonResponse(data)
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            check = db.user.find_one({'username': username, 'password': password})
            if check:
                # request.session['username'] = username
                db.user_logged.update_one({"username":username}, {"$set":{"status":1}})
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
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            # request.session.flush()
            db.user_logged.update_one({"username":username}, {"$set":{"status":0}})
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
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friends=db.user_friend.find({"sourceId":username, "type":"close"}, {"_id":0, "targetId":1})
            followers=db.user_follow.find({"sourceId":username}, {"_id":0, "targetId":1})            
            poeple=list()
            for friend in friends:
                poeple.append(friend['targetId'])
            for follower in followers:
                poeple.append(follower['targetId'])
            poeple.append(username)
            people=list(set(poeple))
            posts=db.user_post.find({"userId":{'$in':people}}).sort("postedAt", -1).limit(10)
            data=[]
            for post in posts:
                post['_id']=str(post['_id'])
                data.append(post)
            print(data)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def fetch_my_posts(request):
    if request.method == 'POST' or request.method == 'GET':
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            posts=db.user_post.find({"userId":username}).sort("postedAt", -1).limit(10)
            data=[]
            for post in posts:
                post['_id']=str(post['_id'])
                data.append(post)
            print(data)
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
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            data=dict()
            data['userId'] = username
            data['caption'] = request.POST.get('caption')
            image = request.FILES.get('image')
            print(image)
            data['imagePath'] = store_image(image, 'post_images')
            data['postedAt'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            data['likes'] = 0
            data['likedBy'] = list()
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
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
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
        # username = request.session.get('username', False)
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
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
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            targetId = request.POST.get('targetId')
            messages_list=[]
            messages=db.user_message.find({"sourceId":username, "targetId":targetId}).sort("sentAt", -1).limit(10)
            for message in messages:
                message['_id']=str(message['_id'])
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
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
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

@csrf_exempt
def fetch_status(request):
    if request.method == 'POST' or request.method == 'GET':
        username = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            status=db.user_status.find({"userId":username}, {"_id":0})
            return JsonResponse(status, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def store_status(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            image = request.FILES.get('image')
            imagePath = store_image(image, 'post_images')
            timeStamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            status = db.user.update_one({"username":username}, {"$set":{"imagePath":imagePath}})
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
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
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

@csrf_exempt
def update_profile_pic(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            image = request.FILES.get('image')
            imagePath = store_image(image, 'profile_images')
            status = db.user.update_one({"username":username}, {"$set":{"imagePath":imagePath}})
            if status:
                data = {'status': 'success', 'message': 'Profile picture updated successfully'}
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
def update_bio(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            bio = request.POST.get('bio')
            status = db.user.update_one({"username":username}, {"$set":{"bio":bio}})
            if status:
                data = {'status': 'success', 'message': 'Bio updated successfully'}
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
def update_email(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            email = request.POST.get('email')
            status = db.user.update_one({"username":username}, {"$set":{"email":email}})
            if status:
                data = {'status': 'success', 'message': 'Mail updated successfully'}
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
def update_phone(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            phone = request.POST.get('phone')
            status = db.user.update_one({"username":username}, {"$set":{"phone":phone}})
            if status:
                data = {'status': 'success', 'message': 'Phone updated successfully'}
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
def update_password(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            password = request.POST.get('password')
            status = db.user.update_one({"username":username}, {"$set":{"password":password}})
            if status:
                data = {'status': 'success', 'message': 'Password updated successfully'}
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
def update_name(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            fullname = request.POST.get('fullname')
            status = db.user.update_one({"username":username}, {"$set":{"fullname":fullname}})
            if status:
                data = {'status': 'success', 'message': 'Name updated successfully'}
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
def like_post(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            postedAt = request.POST.get('postedAt')
            likes = db.user_post.find_one({"username":username, "postedAt":postedAt}, {"likes":1})
            status = db.user_post.update_one({"username":username, "postedAt":postedAt}, {"$set":{"likes":likes+1}, "$push":{"likedBy":username}})      # $push is used to add a value to an array
            if status:
                data = {'status': 'success', 'message': 'Post liked successfully'}
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
def unlike_post(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            postedAt = request.POST.get('postedAt')
            likes = db.user_post.find_one({"username":username, "postedAt":postedAt}, {"likes":1})
            status = db.user_post.update_one({"username":username, "postedAt":postedAt}, {"$set":{"likes":likes+1}, "$pull":{"likedBy":username}})      # $pull is used to remove the username from the array
            if status:
                data = {'status': 'success', 'message': 'Post unliked successfully'}
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
def fetch_friends(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friends = db.user_friend.find({"$or":[{"sourceId":username},{"targetId":username}], "status":"accepted"})
            data = []
            for friend in friends:
                data.append(friend)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def send_friend_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            status = db.user_friend.insert_one({"sourceId":username, "targetId":friend_username, "status":"pending"})
            if status:
                data = {'status': 'success', 'message': 'Friend request sent successfully'}
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
def accept_friend_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            createdAt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            type = "normal"
            status = db.user_friend.update({"sourceId":friend_username, "targetId":username}, {"$set":{"status":"accepted", "createdAt":createdAt, "type":type}})
            if status:
                data = {'status': 'success', 'message': 'Friend request accepted successfully'}
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
def reject_friend_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            status = db.user_friend.update({"sourceId":friend_username, "targetId":username}, {"$set":{"status":"rejected"}})
            if status:
                data = {'status': 'success', 'message': 'Friend request rejected successfully'}
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
def cancel_friend_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            status = db.user_friend.update({"sourceId":username, "targetId":friend_username}, {"$set":{"status":"cancelled"}})
            if status:
                data = {'status': 'success', 'message': 'Friend request cancelled successfully'}
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
def fetch_sent_friend_requests(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_requests = db.user_friend.find({"sourceId":username, "status":"pending"}, {"_id":0})
            data = []
            for friend_request in friend_requests:
                data.append(friend_request)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def fetch_received_friend_requests(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_requests = db.user_friend.find({"targetId":username, "status":"pending"}, {"_id":0})
            data = []
            for friend_request in friend_requests:
                data.append(friend_request)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

    
    
@csrf_exempt
def normal_to_close_friend(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            updatedAt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            status = db.user_friend.update({"$or":[{"sourceId":username, "targetId":friend_username}, {"sourceId":friend_username, "targetId":username}]}, {"$set":{"type":"close", "updatedAt":updatedAt}})
            if status:
                data = {'status': 'success', 'message': friend_username + ' is now your close friend'}
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
def close_to_normal_friend(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            updatedAt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            status = db.user_friend.update({"$or":[{"sourceId":username, "targetId":friend_username}, {"sourceId":friend_username, "targetId":username}]}, {"$set":{"type":"normal", "updatedAt":updatedAt}})
            if status:
                data = {'status': 'success', 'message': friend_username + ' is now your normal friend'}
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
def unfriend(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            friend_username = request.POST.get('friend_username')
            updatedAt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            status = db.user_friend.remove({"sourceId":username, "targetId":friend_usernam, "status":"accepted"}, {"$set":{"status":"unfriended", "updatedAt":updatedAt}})
            if status:
                data = {'status': 'success', 'message': 'Unfriended successfully'}
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
def fetch_followers(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            followers = db.user_follow.find({"targetId":username, "status":"accepted"}, {"_id":0})
            data = []
            for follower in followers:
                data.append(follower)
            print(data)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def fetch_following(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            following = db.user_follow.find({"sourceId":username, "status":"accepted"}, {"_id":0})            
            data = []
            for follow in following:
                data.append(follow)
            print(data)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def fetch_follow_requests(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            print(username)
            follow_requests = db.user_follow.find({"targetId":username, "status":"pending"}, {"_id":0})
            print(follow_requests)
            data = []
            for follow_request in follow_requests:
                data.append(follow_request)
            print(data)
            return JsonResponse(data, safe=False)
        else:
            data = {'status': 'error', 'message': 'Not logged in'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'message': 'Invalid request'}
        return JsonResponse(data)

@csrf_exempt
def follow_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            follow_username = request.POST.get('follow_username')
            message = request.POST.get('message')
            # print(follow_username)
            follow_user_is_public = db.user.find_one({"username":follow_username, "type": "public"})
            # print(follow_user_is_public)
            if follow_user_is_public:
                status = db.user_follow.insert_one({"sourceId":username, "targetId":follow_username, "message":message, "status":"accepted"})
                data = {'status': 'success', 'message': 'Followed successfully'}
            else:
                status = db.user_follow.insert_one({"sourceId":username, "targetId":follow_username, "message":message, "status":"pending"})
                data = {'status': 'success', 'message': 'Follow request sent successfully'}
            if status:
                
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
def accept_follow_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            follow_username = request.POST.get('follow_username')
            createdAt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            status = db.user_follow.update_one({"sourceId":follow_username, "targetId":username, "status":"pending"}, {"$set":{"status":"accepted", "createdAt":createdAt}})
            if status:
                data = {'status': 'success', 'message': 'Follow request accepted successfully'}
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
def reject_follow_request(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            follow_username = request.POST.get('follow_username')
            status = db.user_follow.update_one({"sourceId":follow_username, "targetId":username, "status":"pending"}, {"$set":{"status":"rejected"}})
            if status:
                data = {'status': 'success', 'message': 'Follow request rejected successfully'}
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
def unfollow(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            unfollow_username = request.POST.get('unfollow_username')
            status = db.user_follow.update_one({"sourceId":username, "targetId":unfollow_username, "status":"accepted"}, {"$set":{"status":"unfollowed"}})
            if status:
                data = {'status': 'success', 'message': 'Unfollowed successfully'}
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
def get_image(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            imagPath = request.POST.get('imagePath')
            image = open(imagPath, 'rb')
            if image:
                return FileResponse(image)
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
def change_to_private(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            status = db.user.update_one({"username":username}, {"$set":{"type":"private"}})
            if status:
                data = {'status': 'success', 'message': 'Changed to private successfully'}
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
def change_to_public(request):
    if request.method == 'POST' or request.method == 'GET':
        username  = request.POST.get('username')
        userlogged = db.user_logged.find_one({"username":username, "status":1})
        if userlogged:
            status = db.user.update_one({"username":username}, {"$set":{"type":"public"}})
            if status:
                data = {'status': 'success', 'message': 'Changed to public successfully'}
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


# End of views

# Helper functions
def count_friends(username):
    friends=count(db.user_friend.find({"sourceId":username}))
    return friends

def count_followers(username):
    followers=count(db.user_follow.find({"targetId":username, "status":"accepted"}))
    return followers

def count_following(username):
    following=count(db.user_follow.find({"sourceId":username, "status":"accepted"}))
    return following

def count_posts(username):
    posts=count(db.user_post.find({"userId":username}))
    return posts

def count(obj):
    ct=0
    for ob in obj: ct+=1
    return ct

def store_image(image, subfolder):
    image_name = image.name
    image_extention = image_name.split('.')[-1]
    image_name = str(uuid.uuid4()) + '.' + image_extention
    image_path = os.path.join(settings.MEDIA_ROOT, subfolder, image_name)
    with open(image_path, 'wb+') as file:
        for chunk in image.chunks():
            file.write(chunk)
    return image_path

def delete_image(image_path):
    if os.path.exists(image_path):
        os.remove(image_path)
        return True
    else:
        return False
    








