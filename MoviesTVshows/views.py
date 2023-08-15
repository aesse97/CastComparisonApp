from django.shortcuts import render
from django.conf import settings
import requests
from django.http import JsonResponse
from itertools import combinations

TMDB_API_KEY = settings.TMDB_API_KEY
BASE_URL = 'https://api.themoviedb.org/3'

def search(query, category='movie'):
    url = f"{BASE_URL}/search/{category}?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url)
    data = response.json()
    return data['results']

def get_cast(id, category='movie', top_billed=False):
    endpoint = "aggregate_credits" if category == "tv" else "credits"
    url = f"{BASE_URL}/{category}/{id}/{endpoint}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    cast_list = []
    for person in data['cast'][:5] if top_billed else data['cast']:
        actor_name = person['name']
        character_name = ', '.join([role['character'] for role in person.get('roles', [])]) if 'roles' in person else person.get('character', 'N/A')
        cast_list.append({'actor': actor_name, 'character': character_name or 'N/A'})  # Ensure 'character' key always exists

    return cast_list

def get_common_cast_for_two_titles(cast1, cast2):
    common = []
    for actor_info1 in cast1:
        for actor_info2 in cast2:
            if actor_info1['actor'] == actor_info2['actor']:
                character1 = actor_info1.get('character', 'N/A')
                character2 = actor_info2.get('character', 'N/A')
                merged_actor_info = {
                    'actor': actor_info1['actor'],
                    'characters': list(set([character1, character2]))
                }
                common.append(merged_actor_info)
                break
    return common

def home(request):
    titles = request.POST.getlist('title[]')
    categories = request.POST.getlist('category[]')

    top_billed_casts = []
    full_casts = []

    if not titles:
        return render(request, 'home.html', {
            'error_message': 'Please enter at least one title to compare.'
        })

    for i, title in enumerate(titles):
        search_results = search(title, categories[i])
        if not search_results:
            continue

        title_data = search_results[0]
        top_billed_casts.append(get_cast(title_data['id'], categories[i], top_billed=True))
        full_casts.append(get_cast(title_data['id'], categories[i]))

    if not full_casts:
        return render(request, 'home.html', {
            'error_message': 'Unable to fetch cast details for the given titles.'
        })

    comparisons = {}
    for r in range(2, len(full_casts) + 1):
        for subset in combinations(range(len(full_casts)), r):
            common_cast_dict = {actor_info['actor']: {titles[subset[0]]: actor_info['character']} for actor_info in
                                full_casts[subset[0]]}

            for i in subset[1:]:
                for actor_info in full_casts[i]:
                    if actor_info['actor'] in common_cast_dict:
                        common_cast_dict[actor_info['actor']][titles[i]] = actor_info['character']

            common_cast_dict = {actor: chars for actor, chars in common_cast_dict.items() if len(chars) == r}

            if common_cast_dict:
                comparison_titles = [titles[i] for i in subset]
                comparisons[tuple(comparison_titles)] = common_cast_dict

    combined = zip(titles, top_billed_casts)
    return render(request, 'home.html', {
        'combined': combined,
        'comparisons': comparisons,
        'titles': titles
    })

def autocomplete(request):
    query = request.GET.get('term')
    category = request.GET.get('category', 'movie')
    titles = search(query, category)
    title_names = [title['title'] if category == 'movie' else title['name'] for title in titles]
    return JsonResponse(title_names, safe=False)