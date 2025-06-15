from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import ChatmessageCreateForm

@login_required
def chat_view(request, chatroom_name='public'):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:30]
    form = ChatmessageCreateForm()
    
    other_user = None 
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break
    
    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid:
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message': message,
                'user': request.user
            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)
        
    context = {
        'chat_messages': chat_messages, 
        'form': form,
        'other_user': other_user,
        'chatroom_name': chatroom_name
    }
    return render(request, 'a_rtchat/chat.html', context)


@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')  

    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404("User not found")

    chatroom = (
        ChatGroup.objects
        .filter(is_private=True, members=request.user)
        .filter(members=other_user)
        .first()
    )

    if not chatroom:
        chatroom = ChatGroup.objects.create(
            is_private=True,
            group_name=f"private_{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}"
        )
        chatroom.members.add(request.user, other_user)

    return redirect('chatroom', chatroom_name=chatroom.group_name)