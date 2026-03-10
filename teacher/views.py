# from django.shortcuts import render

# # Create your views here.
# def server(request):
#     return render(request,'server.html')

from django.shortcuts import render, redirect
from .models import Teacher
from student.models import Proposal

def login(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        password = request.POST.get('password')

        try:
            teacher = Teacher.objects.get(roll_no=roll_no)
            if teacher.password != password:
                return render(request, 'teacher_login.html', {'error': 'Invalid password'})

            request.session['teacher_roll_no'] = teacher.roll_no
            request.session['teacher_name'] = teacher.name
            return redirect('/teacher/dashboard')

        except Teacher.DoesNotExist:
            return render(request, 'teacher_login.html', {'error': 'No account found'})

    return render(request, 'teacher_login.html')


def dashboard(request):
    if 'teacher_roll_no' not in request.session:
        return redirect('/teacher/login')

    status_filter = request.GET.get('status', 'All')

    if status_filter == 'All':
        proposals = Proposal.objects.all().order_by('-submitted_at')
    else:
        proposals = Proposal.objects.filter(status=status_filter).order_by('-submitted_at')

    return render(request, 'teacher_dashboard.html', {
        'proposals': proposals,
        'teacher_name': request.session['teacher_name'],
        'status_filter': status_filter,
        'total': Proposal.objects.count(),
        'pending': Proposal.objects.filter(status='Pending').count(),
        'approved': Proposal.objects.filter(status='Approved').count(),
        'rejected': Proposal.objects.filter(status='Rejected').count(),
    })


def review_proposal(request, proposal_id):
    if 'teacher_roll_no' not in request.session:
        return redirect('/teacher/login')

    proposal = Proposal.objects.get(id=proposal_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        feedback = request.POST.get('feedback')

        proposal.status = status
        proposal.feedback = feedback
        proposal.save()

        return redirect('/teacher/dashboard')

    return render(request, 'teacher_review.html', {'proposal': proposal})


def logout(request):
    request.session.flush()
    return redirect('/teacher/login')


def students_list(request):
    if 'teacher_roll_no' not in request.session:
        return redirect('/teacher/login')

    from accounts.models import Register
    from student.models import Proposal

    filter_type = request.GET.get('filter', 'All')
    all_students = Register.objects.all().order_by('roll_no')

    student_data = []
    for student in all_students:
        proposal = Proposal.objects.filter(roll_no=student.roll_no).first()
        has_proposal = proposal is not None

        if filter_type == 'Submitted' and not has_proposal:
            continue
        if filter_type == 'Not Submitted' and has_proposal:
            continue

        student_data.append({
            'name': f"{student.fname} {student.lname}",
            'roll_no': student.roll_no,
            'program': student.program,
            'section': student.section,
            'has_proposal': has_proposal,
            'proposal_id': proposal.id if proposal else None,
        })

    total = Register.objects.count()
    submitted = sum(1 for s in student_data if s['has_proposal'])

    return render(request, 'teacher_students.html', {
        'students': student_data,
        'teacher_name': request.session['teacher_name'],
        'filter': filter_type,
        'total_students': total,
        'submitted_count': Proposal.objects.values('roll_no').distinct().count(),
        'not_submitted_count': total - Proposal.objects.values('roll_no').distinct().count(),
    })


def delete_student(request, roll_no):
    if 'teacher_roll_no' not in request.session:
        return redirect('/teacher/login')
    if request.method == 'POST':
        from accounts.models import Register
        from student.models import Proposal
        Proposal.objects.filter(roll_no=roll_no).delete()
        Register.objects.filter(roll_no=roll_no).delete()
    return redirect('/teacher/students')
      