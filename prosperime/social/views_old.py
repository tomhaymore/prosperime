
# Deletes FollowThread object between given thread + user
def unfollowThread(request):
	response = {}

	try:
		thread = Thread.objects.get(id=request.POST.get("thread_id"))
	except:
		response = {
			"result":"failure",
			"errors":"No thread id or thread not found"
		}
		return HttpResponse(json.dumps(response))

	try:
		follow = FollowThread.objects.get(thread=thread, user=request.user)
		follow.delete()

		response = {
			"result":"success",
		}

	except:
		response = {
			"result":"failure",
			"errors":"Error writing to DB",
		}


	return HttpResponse(json.dumps(response))


# Adds a comment to a given thread
def postComment(request):
	response = {}
	try:
		thread = Thread.objects.get(id=request.POST.get("thread_id"))
		body = request.POST.get("body")
	except:
		response = {
			"result":"failure",
			"errors":"Can't find thread or missing data from template"
		}
		return HttpResponse(json.dumps(response))


	print body

	# id, owner_pic, owner_name, created


	response["result"] = "success"
	response["data"] = {
		"id":1,
		"owner_pic":request.user.profile.default_profile_pic(),
		"owner_name":request.user.profile.first_name,
		"created":helpers._formatted_date(datetime.datetime.now())
	}
	

	return HttpResponse(json.dumps(response))


def saveComment(request):

	response = {}

	if not request.POST:
		response["result"] = "failure"
		response["errors"] = "Incorrect request type"
		return HttpResponse(json.dumps(response))

	body = request.POST.get("body")
	path_id = request.POST.get("path_id")
	comment_type = request.POST.get("type")

	## Check all params, save comment, 
	##	then send back data needed to update DOM
	if len(body) > 0 and int(path_id) > 0 and len(comment_type) > 0:
		try:
			c = Comment()
			c.owner = request.user
			c.path = SavedPath.objects.get(pk=int(path_id))
			c.type = comment_type
			c.body = body
			c.save()
		except:
			response = {
				"result":"failure",
				"errors":"Error creating comment @ db level"
			}
			return HttpResponse(json.dumps(response))
	else:
		response = {
			"result":"failure",
			"errors":"one or more blank parameters"
		}
		return HttpResponse(json.dumps(response))

	response["user_name"] = request.user.profile.full_name()
	response["profile_pic"] = request.user.profile.default_profile_pic()
	response["date_created"] = helpers._formatted_date(c.created) ## need to format this
	response["result"] = "success"

	return HttpResponse(json.dumps(response))

## DEPRECATED: keep around for now for code review
def thread(request, thread_id):
	thread = Thread.objects.get(id=thread_id)
	comments = Comment.objects.filter(thread=thread).order_by("index")


	owner_positions = comments[0].owner.positions.all().order_by('-start_date').exclude(type="education")
	if owner_positions.exists():
		owner_current_position = {"title":owner_positions[0].title, "entity_id":owner_positions[0].id, "entity_logo":owner_positions[0].entity.default_logo()}
	else:
		owner_current_position = None

	if request.user in thread.followers.all():
		is_following = True
	else:
		is_following = False

	total_followers = thread.followers.all().count()
	## TODO: implement way to get "# followers from your network"
	network_followers = total_followers

	data = {
		"thread_id":thread_id,
		"is_following":is_following,
		"total_followers":total_followers,
		"network_followers":network_followers,
		"comments":[{"owner_name":c.owner.profile.first_name, "owner_id":c.owner.id, "owner_pic":c.owner.profile.default_profile_pic(), "goal":c.meta, "body":c.body, "id":c.id, "votes":Vote.objects.filter(owner=c.owner).count(), "created":helpers._formatted_date(c.created), "modified":helpers._formatted_date(c.updated)} for c in comments],
		"owner_current_position":owner_current_position,
	}


	return render_to_response("social/thread.html",data,context_instance=RequestContext(request))

## DEPRECATED: keep around for now for code review
def create_thread(request):

	data = {}
	data["foo"] = "bar"
	return render_to_response("social/createThread.html", data, context_instance=RequestContext(request))





	