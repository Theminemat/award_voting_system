from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Person, Category, VotingCode, Vote, VotingSession, VoteStatistics
import re
from django.conf import settings
from .mailgun_utils import send_mailgun_template_email



def index(request):
    return render(request, 'voting/index.html')


def vote(request, code=None):
    voting_code = None
    if code:
        try:
            voting_code = VotingCode.objects.get(code=code, is_active=True)
            if not voting_code.can_vote():
                messages.error(request, 'Dieser Code wurde bereits vollständig verwendet oder ist nicht mehr gültig.')
                return redirect('voting:index')
        except VotingCode.DoesNotExist:
            messages.error(request, 'Ungültiger Voting-Code.')
            return redirect('voting:index')

    # Handle code submission from form
    if request.method == 'POST' and 'voting_code' in request.POST:
        submitted_code = request.POST.get('voting_code', '').strip().upper()
        if submitted_code:
            try:
                voting_code = VotingCode.objects.get(code=submitted_code, is_active=True)
                if not voting_code.can_vote():
                    messages.error(request,
                                   'Dieser Code wurde bereits vollständig verwendet oder ist nicht mehr gültig.')
                    return render(request, 'voting/vote.html')
                return redirect('voting:vote_with_code', code=submitted_code)
            except VotingCode.DoesNotExist:
                messages.error(request, 'Ungültiger Voting-Code.')
                return render(request, 'voting/vote.html')

    if not voting_code:
        return render(request, 'voting/vote.html')

    session, created = VotingSession.objects.get_or_create(
        voting_code=voting_code,
        defaults={
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500]
        }
    )

    # Check if session is already completed
    if session.is_completed:
        messages.info(request, 'Du hast bereits mit diesem Code abgestimmt.')
        return redirect('voting:success')

    # Handle form submission (vote, go back)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'previous':
            session.regress_category()
            return redirect('voting:vote_with_code', code=voting_code.code)

        elif action == 'next':
            current_category_for_vote = session.get_current_category()
            person_id = request.POST.get('person_id')

            if not person_id:
                messages.error(request, 'Bitte wähle eine Person aus, um fortzufahren.')
            else:
                try:
                    person = Person.objects.get(id=person_id)
                    session.add_vote(current_category_for_vote.id, person.id)

                    if session.is_final_category():
                        if session.complete_voting():
                            return redirect('voting:success')
                        else:
                            messages.error(request, 'Fehler beim Abschließen der Abstimmung.')
                    else:
                        session.advance_category()
                        return redirect('voting:vote_with_code', code=voting_code.code)

                except Person.DoesNotExist:
                    messages.error(request, 'Ungültige Personenauswahl.')

    current_category = session.get_current_category()
    if not current_category:
        if session.complete_voting():
            return redirect('voting:success')
        else:
            messages.error(request, 'Fehler beim Abschließen der Abstimmung.')
            return redirect('voting:index')

    persons = Person.objects.all().order_by('first_name', 'last_name')

    all_categories = session.get_categories()

    progress_percentage = ((session.current_category_index) / len(all_categories)) * 100 if all_categories else 0

    selected_person_id = session.pending_votes.get(str(current_category.id))

    context = {
        'voting_code': voting_code,
        'session': session,
        'current_category': current_category,
        'persons': persons,
        'all_categories': all_categories,
        'progress_percentage': progress_percentage,
        'current_step': session.current_category_index + 1,
        'total_steps': len(all_categories),
        'is_final_category': session.is_final_category(),
        'selected_person_id': selected_person_id,
    }

    return render(request, 'voting/vote_sequential.html', context)


def success(request):
    return render(request, 'voting/success.html')


@login_required
def results(request):
    if not request.user.is_staff:
        messages.error(request, 'Zugriff verweigert. Nur für Administratoren.')
        return redirect('voting:index')

    categories = Category.objects.filter(is_active=True).order_by('title')
    results_data = {}

    for category in categories:
        # Get top 5 results for this category
        top_results = VoteStatistics.objects.filter(category=category).order_by('-vote_count', 'person__first_name')[:5]
        total_votes = Vote.objects.filter(category=category).count()

        results_data[category] = {
            'top_results': top_results,
            'total_votes': total_votes
        }

    context = {
        'results': results_data
    }

    return render(request, 'voting/results.html', context)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# NEUE VIEW
@login_required
def send_codes_to_list(request):

    if not request.user.is_staff:
        messages.error(request, 'Zugriff verweigert. Nur für Administratoren.')
        return redirect('voting:index')

    if request.method == 'POST':
        emails_raw = request.POST.get('emails', '')
        # Split by newlines, commas, or spaces and filter out empty strings
        email_list = [email.strip() for email in re.split(r'[\n,;\s]+', emails_raw) if email.strip()]

        if not email_list:
            messages.error(request, 'Bitte geben Sie mindestens eine E-Mail-Adresse ein.')
            return redirect('voting:send_codes_to_list')

        sent_count = 0
        failed_emails = []

        for email in email_list:
            try:
                # Generate a unique code with max_uses=1
                voting_code = VotingCode.generate_code(
                    user=request.user,
                    max_uses=1,
                    email=email
                )


                vote_url = f"{settings.VOTE_BASE_URL}{voting_code.code}"


                template_variables = {
                    'vote_url': vote_url,
                    'voting_code': voting_code.code,
                }

                subject = 'Deine Einladung zur Klassenabstimmung'
                if send_mailgun_template_email(
                    to_email=email,
                    subject=subject,
                    template_name=settings.MAILGUN_TEMPLATE_NAME,
                    template_variables=template_variables
                ):
                    sent_count += 1
                else:
                    failed_emails.append(email)

            except Exception as e:
                failed_emails.append(email)

        if sent_count > 0:
            messages.success(request, f'{sent_count} Einladungen wurden erfolgreich versendet.')
        if failed_emails:
            messages.error(request, f'Konnte keine E-Mails an folgende Adressen senden: {", ".join(failed_emails)}')

        return redirect('voting:send_codes_to_list')

    return render(request, 'voting/admin_send_codes.html')



def live_results(request):
    """
    Zeigt die öffentliche Live-Ergebnisseite an, die sich automatisch aktualisiert.
    """
    return render(request, 'voting/live_results.html')


def live_results_data(request):

    completed_voters = VotingSession.objects.filter(is_completed=True).count()

    data = {
        'total_votes': completed_voters
    }

    return JsonResponse(data)